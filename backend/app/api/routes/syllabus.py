from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.models.syllabus import Syllabus, Chapter
from app.models.note import Note
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.matching_service import match_note_to_chapters, detect_gaps, embedding_to_str, embed_text
import os
import json

router = APIRouter()


class ChapterIn(BaseModel):
    unit_number: int
    title: str
    description: str = ""


class SyllabusCreate(BaseModel):
    title: str
    subject: str
    semester: str = ""
    chapters: list[ChapterIn] = []


class SyllabusFromText(BaseModel):
    title: str
    subject: str
    semester: str = ""
    syllabus_text: str


class MatchRequest(BaseModel):
    note_text: str
    chapters: list[dict]
    threshold: float = 0.3


class GapRequest(BaseModel):
    chapters: list[dict]
    matched_chapter_ids: list[int]


# ── AI Syllabus Parser ────────────────────────────────────────────

@router.post("/parse-text")
def parse_syllabus_from_text(
    data: SyllabusFromText,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Paste your syllabus text — AI splits it into individual topic chapters automatically.
    """
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")

    prompt = f"""You are a university syllabus parser. 

Extract every individual TOPIC from this syllabus text and return them as a JSON array.
Each topic should be a separate chapter — do NOT group multiple topics together.

For example if the syllabus says "Constrained Optimization: Lagrange Multipliers, KKT Conditions"
you should create TWO separate chapters:
- "Lagrange Multipliers"  
- "KKT Conditions (Karush-Kuhn-Tucker)"

Syllabus text:
{data.syllabus_text}

Return ONLY a JSON array like this, no other text:
[
  {{"unit_number": 1, "title": "Topic Name", "description": "brief one line description"}},
  {{"unit_number": 2, "title": "Another Topic", "description": "brief one line description"}}
]

Rules:
- Each individual topic = one chapter
- unit_number starts from 1 and increments
- title should be the specific topic name
- description should be one sentence explaining what it covers
- Maximum 30 chapters
- Return ONLY the JSON array, no markdown, no explanation"""

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000,
        )

        raw = response.choices[0].message.content.strip()

        # Clean JSON if wrapped in markdown
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        chapters_data = json.loads(raw)

        # Create syllabus in DB
        syllabus = Syllabus(
            title=data.title,
            subject=data.subject,
            semester=data.semester,
            owner_id=current_user.id,
        )
        db.add(syllabus)
        db.flush()

        for ch in chapters_data:
            embedding = embed_text(f"{ch['title']}. {ch.get('description', '')}")
            chapter = Chapter(
                unit_number=ch["unit_number"],
                title=ch["title"],
                description=ch.get("description", ""),
                embedding=embedding_to_str(embedding),
                syllabus_id=syllabus.id,
            )
            db.add(chapter)

        db.commit()
        db.refresh(syllabus)

        return {
            "id": syllabus.id,
            "title": syllabus.title,
            "subject": syllabus.subject,
            "chapters_created": len(chapters_data),
            "chapters": chapters_data,
            "message": f"Successfully created {len(chapters_data)} chapters from your syllabus text"
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI could not parse the syllabus. Try rephrasing it.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Standard CRUD ─────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_syllabus(
    data: SyllabusCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    syllabus = Syllabus(
        title=data.title,
        subject=data.subject,
        semester=data.semester,
        owner_id=current_user.id,
    )
    db.add(syllabus)
    db.flush()

    for ch in data.chapters:
        embedding = embed_text(f"{ch.title}. {ch.description}")
        chapter = Chapter(
            unit_number=ch.unit_number,
            title=ch.title,
            description=ch.description,
            embedding=embedding_to_str(embedding),
            syllabus_id=syllabus.id,
        )
        db.add(chapter)

    db.commit()
    db.refresh(syllabus)
    return {"id": syllabus.id, "title": syllabus.title, "subject": syllabus.subject}


@router.get("/")
def list_syllabuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    syllabuses = db.query(Syllabus).filter(Syllabus.owner_id == current_user.id).all()
    result = []
    for s in syllabuses:
        chapters = db.query(Chapter).filter(Chapter.syllabus_id == s.id).all()
        result.append({
            "id": s.id,
            "title": s.title,
            "subject": s.subject,
            "semester": s.semester,
            "chapter_count": len(chapters),
            "chapters": [{"id": c.id, "unit_number": c.unit_number, "title": c.title, "description": c.description} for c in chapters],
        })
    return result


@router.get("/{syllabus_id}/gaps")
def get_gaps(
    syllabus_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    syllabus = db.query(Syllabus).filter(
        Syllabus.id == syllabus_id,
        Syllabus.owner_id == current_user.id
    ).first()
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    chapters = db.query(Chapter).filter(Chapter.syllabus_id == syllabus_id).all()
    matched_notes = db.query(Note).filter(
        Note.syllabus_id == syllabus_id,
        Note.chapter_id.isnot(None)
    ).all()

    matched_ids = list(set([n.chapter_id for n in matched_notes]))
    chapters_data = [{"id": c.id, "title": c.title, "description": c.description} for c in chapters]

    return detect_gaps(chapters=chapters_data, matched_chapter_ids=matched_ids)


@router.post("/match-test")
def test_matching(request: MatchRequest):
    result = match_note_to_chapters(
        note_text=request.note_text,
        chapters=request.chapters,
        threshold=request.threshold,
    )
    return result


@router.post("/gap-test")
def test_gap_detection(request: GapRequest):
    return detect_gaps(
        chapters=request.chapters,
        matched_chapter_ids=request.matched_chapter_ids,
    )
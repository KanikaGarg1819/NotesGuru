from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.matching_service import match_note_to_chapters, detect_gaps

router = APIRouter()


# ── Request models ────────────────────────────────────────────────

class Chapter(BaseModel):
    id:          int
    title:       str
    description: str = ""


class MatchRequest(BaseModel):
    note_text: str
    chapters:  list[Chapter]
    threshold: float = 0.3


class GapRequest(BaseModel):
    chapters:            list[Chapter]
    matched_chapter_ids: list[int]


# ── Routes ────────────────────────────────────────────────────────

@router.post("/match-test")
async def test_matching(request: MatchRequest):
    """
    Phase 5 TEST — Match note text to syllabus chapters.

    Send note text + list of chapters.
    Get back the best matching chapter + confidence score.
    """
    if not request.note_text.strip():
        raise HTTPException(status_code=400, detail="note_text cannot be empty")

    if not request.chapters:
        raise HTTPException(status_code=400, detail="chapters list cannot be empty")

    chapters_data = [
        {"id": ch.id, "title": ch.title, "description": ch.description}
        for ch in request.chapters
    ]

    result = match_note_to_chapters(
        note_text=request.note_text,
        chapters=chapters_data,
        threshold=request.threshold,
    )
    return result


@router.post("/gap-test")
async def test_gap_detection(request: GapRequest):
    """
    Phase 5 TEST — Detect which chapters have no notes.

    Send all chapters + list of matched chapter IDs.
    Get back coverage percentage + list of gaps.
    """
    chapters_data = [
        {"id": ch.id, "title": ch.title, "description": ch.description}
        for ch in request.chapters
    ]

    result = detect_gaps(
        chapters=chapters_data,
        matched_chapter_ids=request.matched_chapter_ids,
    )
    return result


@router.get("/")
async def list_syllabuses():
    return {"syllabuses": [], "message": "Syllabus endpoint ready"}
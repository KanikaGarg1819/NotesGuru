from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.note import Note, NoteStatus
from app.models.guide import Guide
from app.models.syllabus import Syllabus, Chapter
from app.services.image_processor import preprocess_image
from app.services.ocr_service import extract_text
from app.tasks.ocr_task import process_note_task

router = APIRouter()


@router.post("/preprocess-test")
async def test_preprocessing(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    image_bytes = await file.read()
    result = preprocess_image(image_bytes)
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["message"])
    return Response(
        content=result["cleaned_image"],
        media_type="image/png",
        headers={"X-Original-Size": result["original_size"]},
    )


@router.post("/ocr-test")
async def test_ocr(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    image_bytes = await file.read()
    preprocessed = preprocess_image(image_bytes)
    if not preprocessed["success"]:
        raise HTTPException(status_code=422, detail=preprocessed["message"])
    ocr_result = extract_text(preprocessed["cleaned_image"])
    return {
        "success": ocr_result["success"],
        "text": ocr_result["text"],
        "ocr_source": ocr_result["source"],
        "char_count": len(ocr_result["text"]),
    }


@router.post("/process")
async def process_note(
    file: UploadFile = File(...),
    syllabus_id: int = 1,
    subject: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    chapters = []
    syllabus = db.query(Syllabus).filter(
        Syllabus.id == syllabus_id,
        Syllabus.owner_id == current_user.id
    ).first()

    if syllabus:
        db_chapters = db.query(Chapter).filter(Chapter.syllabus_id == syllabus_id).all()
        chapters = [{"id": c.id, "title": c.title, "description": c.description or ""} for c in db_chapters]

    if not chapters:
        chapters = [
            {"id": 1, "title": "General Notes", "description": ""},
            {"id": 2, "title": "Key Concepts", "description": ""},
            {"id": 3, "title": "Definitions", "description": ""},
        ]

    image_bytes = await file.read()
    image_hex = image_bytes.hex()

    task = process_note_task.delay(
        image_bytes_hex=image_hex,
        chapters=chapters,
        subject=subject,
    )

    actual_syllabus_id = syllabus_id if syllabus else None
    note = Note(
        image_url=f"task:{task.id}",
        status=NoteStatus.PENDING,
        owner_id=current_user.id,
        syllabus_id=actual_syllabus_id,
    )
    db.add(note)
    db.commit()

    return {
        "task_id": task.id,
        "note_id": note.id,
        "status": "queued",
        "message": "Note is being processed. Poll /notes/status/{task_id} for result.",
    }


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.tasks.worker import celery_app
    task = celery_app.AsyncResult(task_id)

    if task.state == "PENDING":
        return {"task_id": task_id, "status": "pending", "percent": 0}

    if task.state == "PROGRESS":
        meta = task.info or {}
        return {
            "task_id": task_id,
            "status": "processing",
            "step": meta.get("step", ""),
            "percent": meta.get("percent", 0),
        }

    if task.state == "SUCCESS":
        result = task.result
        if result.get("success"):
            note = db.query(Note).filter(Note.image_url == f"task:{task_id}").first()
            if note:
                note.raw_text = result.get("note_text", "")
                note.cleaned_text = result.get("note_text", "")
                note.match_score = result.get("match_score", 0)
                note.status = NoteStatus.MATCHED if result.get("matched") else NoteStatus.UNMATCHED
                note.chapter_id = result.get("chapter_id")
                db.flush()
                existing = db.query(Guide).filter(Guide.note_id == note.id).first()
                if not existing and result.get("guide_content"):
                    guide = Guide(
                        title=result.get("chapter_title", "Study Guide"),
                        content=result.get("guide_content", ""),
                        chapter_name=result.get("chapter_title", ""),
                        owner_id=current_user.id,
                        note_id=note.id,
                    )
                    db.add(guide)
                db.commit()
        return {"task_id": task_id, "status": "done", "result": result}

    if task.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(task.info)}

    return {"task_id": task_id, "status": task.state}


@router.get("/")
async def list_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notes = db.query(Note).filter(Note.owner_id == current_user.id).order_by(Note.created_at.desc()).all()
    return [{"id": n.id, "status": n.status, "match_score": n.match_score, "created_at": n.created_at.isoformat()} for n in notes]
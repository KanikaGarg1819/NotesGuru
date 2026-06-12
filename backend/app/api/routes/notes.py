from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from app.services.image_processor import preprocess_image
from app.services.ocr_service import extract_text
from app.tasks.ocr_task import process_note_task

router = APIRouter()


@router.post("/preprocess-test")
async def test_preprocessing(file: UploadFile = File(...)):
    """Phase 3 — Upload image, get back cleaned version."""
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
    """Phase 4 — Upload image, get back extracted text."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    image_bytes = await file.read()
    preprocessed = preprocess_image(image_bytes)
    if not preprocessed["success"]:
        raise HTTPException(status_code=422, detail=preprocessed["message"])
    ocr_result = extract_text(preprocessed["cleaned_image"])
    return {
        "success":    ocr_result["success"],
        "text":       ocr_result["text"],
        "ocr_source": ocr_result["source"],
        "char_count": len(ocr_result["text"]),
    }


@router.post("/process")
async def process_note(
    file: UploadFile = File(...),
    syllabus_id: int = 1,
    subject: str = "",
):
    """
    Phase 7 — Full pipeline as background task.
    Upload image → get task_id immediately → poll /notes/status/{task_id} for result.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    image_bytes = await file.read()

    # Convert to hex for Celery serialization
    image_hex = image_bytes.hex()

    # Dummy chapters for now — Phase 10 will pull from DB
    dummy_chapters = [
        {"id": 1, "title": "General Notes",     "description": ""},
        {"id": 2, "title": "Key Concepts",       "description": ""},
        {"id": 3, "title": "Definitions",        "description": ""},
    ]

    # Queue the task
    task = process_note_task.delay(
        image_bytes_hex=image_hex,
        chapters=dummy_chapters,
        subject=subject,
    )

    return {
        "task_id": task.id,
        "status":  "queued",
        "message": "Note is being processed. Poll /notes/status/{task_id} for result.",
    }


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Phase 7 — Poll this endpoint to check background task progress.
    Returns current step + result when done.
    """
    from app.tasks.worker import celery_app
    task = celery_app.AsyncResult(task_id)

    if task.state == "PENDING":
        return {"task_id": task_id, "status": "pending", "percent": 0}

    if task.state == "PROGRESS":
        meta = task.info or {}
        return {
            "task_id": task_id,
            "status":  "processing",
            "step":    meta.get("step", ""),
            "percent": meta.get("percent", 0),
        }

    if task.state == "SUCCESS":
        return {
            "task_id": task_id,
            "status":  "done",
            "result":  task.result,
        }

    if task.state == "FAILURE":
        return {
            "task_id": task_id,
            "status":  "failed",
            "error":   str(task.info),
        }

    return {"task_id": task_id, "status": task.state}


@router.get("/")
async def list_notes():
    return {"notes": [], "message": "Notes endpoint ready"}
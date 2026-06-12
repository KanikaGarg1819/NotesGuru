"""
OCR Background Task
--------------------
Runs the full pipeline (preprocess → OCR → match → generate) as a background job.
Student uploads image → gets a task_id immediately → result ready when done.
"""

from app.tasks.worker import celery_app
from app.services.image_processor import preprocess_image
from app.services.ocr_service import extract_text
from app.services.matching_service import match_note_to_chapters
from app.services.generation_service import generate_study_guide
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.process_note")
def process_note_task(
    self,
    image_bytes_hex: str,
    chapters: list[dict],
    chapter_description: str = "",
    subject: str = "",
):
    """
    Full pipeline as a background task.

    Steps:
    1. Preprocess image
    2. Extract text via OCR
    3. Match to syllabus chapter
    4. Generate study guide

    Returns result dict with all outputs.
    """
    try:
        # Convert hex back to bytes (Celery can't serialize raw bytes)
        image_bytes = bytes.fromhex(image_bytes_hex)

        # Step 1 — Preprocess
        self.update_state(state="PROGRESS", meta={"step": "preprocessing", "percent": 10})
        logger.info("Task: preprocessing image")
        preprocessed = preprocess_image(image_bytes)

        if not preprocessed["success"]:
            return {"success": False, "error": preprocessed["message"], "step": "preprocessing"}

        # Step 2 — OCR
        self.update_state(state="PROGRESS", meta={"step": "ocr", "percent": 30})
        logger.info("Task: extracting text")
        ocr_result = extract_text(preprocessed["cleaned_image"])

        if not ocr_result["success"]:
            return {"success": False, "error": ocr_result["message"], "step": "ocr"}

        note_text = ocr_result["text"]

        # Step 3 — Match
        self.update_state(state="PROGRESS", meta={"step": "matching", "percent": 60})
        logger.info("Task: matching to syllabus")
        match_result = match_note_to_chapters(
            note_text=note_text,
            chapters=chapters,
        )

        # Step 4 — Generate
        self.update_state(state="PROGRESS", meta={"step": "generating", "percent": 80})
        logger.info("Task: generating study guide")

        chapter_title = match_result.get("chapter_title") or "General Notes"
        guide_result  = generate_study_guide(
            note_text=note_text,
            chapter_title=chapter_title,
            chapter_description=chapter_description,
            subject=subject,
        )

        # Done
        self.update_state(state="PROGRESS", meta={"step": "done", "percent": 100})

        return {
            "success":       True,
            "note_text":     note_text,
            "ocr_source":    ocr_result["source"],
            "matched":       match_result["matched"],
            "chapter_id":    match_result["chapter_id"],
            "chapter_title": chapter_title,
            "match_score":   match_result["score"],
            "guide_content": guide_result["content"],
            "step":          "done",
        }

    except Exception as e:
        logger.error(f"Task failed: {e}")
        return {"success": False, "error": str(e), "step": "failed"}
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.generation_service import generate_study_guide, generate_study_guide_stream

router = APIRouter()


class GenerateRequest(BaseModel):
    note_text:           str
    chapter_title:       str
    chapter_description: str = ""
    subject:             str = ""


@router.post("/generate-test")
async def test_generation(request: GenerateRequest):
    """Phase 6 TEST — Generate a study guide from note text + chapter."""
    if not request.note_text.strip():
        raise HTTPException(status_code=400, detail="note_text cannot be empty")
    if not request.chapter_title.strip():
        raise HTTPException(status_code=400, detail="chapter_title cannot be empty")

    result = generate_study_guide(
        note_text=request.note_text,
        chapter_title=request.chapter_title,
        chapter_description=request.chapter_description,
        subject=request.subject,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {
        "success":       result["success"],
        "chapter_title": request.chapter_title,
        "content":       result["content"],
        "model":         result["model"],
        "char_count":    len(result["content"]),
    }


@router.post("/generate-stream")
async def stream_generation(request: GenerateRequest):
    """Phase 6 STREAM — Streams response live word by word."""
    if not request.note_text.strip():
        raise HTTPException(status_code=400, detail="note_text cannot be empty")

    async def stream():
        async for chunk in generate_study_guide_stream(
            note_text=request.note_text,
            chapter_title=request.chapter_title,
            chapter_description=request.chapter_description,
            subject=request.subject,
        ):
            yield chunk

    return StreamingResponse(stream(), media_type="text/plain")


@router.get("/")
async def list_guides():
    return {"guides": [], "message": "Guides endpoint ready"}
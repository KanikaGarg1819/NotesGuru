from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.models.guide import Guide
from app.models.note import Note
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.generation_service import generate_study_guide, generate_study_guide_stream

router = APIRouter()


class GenerateRequest(BaseModel):
    note_text: str
    chapter_title: str
    chapter_description: str = ""
    subject: str = ""


@router.get("/")
def list_guides(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    guides = db.query(Guide).filter(Guide.owner_id == current_user.id).order_by(Guide.created_at.desc()).all()
    return [
        {
            "id": g.id,
            "title": g.title,
            "chapter_name": g.chapter_name,
            "created_at": g.created_at.isoformat(),
            "content_preview": g.content[:200] + "..." if len(g.content) > 200 else g.content,
        }
        for g in guides
    ]


@router.get("/{guide_id}")
def get_guide(
    guide_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    guide = db.query(Guide).filter(
        Guide.id == guide_id,
        Guide.owner_id == current_user.id
    ).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    return {
        "id": guide.id,
        "title": guide.title,
        "chapter_name": guide.chapter_name,
        "content": guide.content,
        "created_at": guide.created_at.isoformat(),
    }


@router.post("/generate-test")
def test_generation(request: GenerateRequest):
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
        "success": result["success"],
        "chapter_title": request.chapter_title,
        "content": result["content"],
        "model": result["model"],
        "char_count": len(result["content"]),
    }


@router.post("/generate-stream")
async def stream_generation(request: GenerateRequest):
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
from pydantic import BaseModel
from datetime import datetime
from app.models.note import NoteStatus


# ── Note ──────────────────────────────────────────────────────────

class NoteOut(BaseModel):
    id:           int
    image_url:    str
    raw_text:     str | None
    cleaned_text: str | None
    match_score:  float | None
    status:       NoteStatus
    created_at:   datetime
    chapter_id:   int | None

    model_config = {"from_attributes": True}


# ── Guide ─────────────────────────────────────────────────────────

class GuideOut(BaseModel):
    id:           int
    title:        str
    content:      str        # Markdown
    chapter_name: str | None
    created_at:   datetime
    note_id:      int

    model_config = {"from_attributes": True}
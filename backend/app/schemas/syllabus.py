from pydantic import BaseModel
from datetime import datetime


# ── Chapter ───────────────────────────────────────────────────────

class ChapterCreate(BaseModel):
    unit_number: int
    title:       str
    description: str | None = None


class ChapterOut(BaseModel):
    id:          int
    unit_number: int
    title:       str
    description: str | None

    model_config = {"from_attributes": True}


# ── Syllabus ──────────────────────────────────────────────────────

class SyllabusCreate(BaseModel):
    title:    str
    subject:  str
    semester: str | None = None
    chapters: list[ChapterCreate] = []


class SyllabusOut(BaseModel):
    id:         int
    title:      str
    subject:    str
    semester:   str | None
    created_at: datetime
    chapters:   list[ChapterOut] = []

    model_config = {"from_attributes": True}
from datetime import datetime
from sqlalchemy import String, Text, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
import enum


class NoteStatus(str, enum.Enum):
    PENDING    = "pending"     # just uploaded, not processed yet
    PROCESSING = "processing"  # OCR / matching running
    MATCHED    = "matched"     # successfully matched to a chapter
    UNMATCHED  = "unmatched"   # no good chapter match found
    FAILED     = "failed"      # something went wrong


class Note(Base):
    """
    A note is one uploaded image of handwritten notes.
    After processing it has extracted text + a matched chapter.
    """
    __tablename__ = "notes"

    id:             Mapped[int]   = mapped_column(primary_key=True, index=True)
    image_url:      Mapped[str]   = mapped_column(String(500), nullable=False)  # S3 URL
    raw_text:       Mapped[str]   = mapped_column(Text,        nullable=True)   # OCR output
    cleaned_text:   Mapped[str]   = mapped_column(Text,        nullable=True)   # after cleanup
    match_score:    Mapped[float] = mapped_column(Float,       nullable=True)   # 0.0 → 1.0
    status:         Mapped[NoteStatus] = mapped_column(
                        Enum(NoteStatus), default=NoteStatus.PENDING
                    )
    created_at:     Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at:   Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Foreign keys
    owner_id:    Mapped[int] = mapped_column(ForeignKey("users.id"),      nullable=False)
    syllabus_id: Mapped[int] = mapped_column(ForeignKey("syllabuses.id"), nullable=False)
    chapter_id:  Mapped[int] = mapped_column(ForeignKey("chapters.id"),   nullable=True)

    # Relationships
    owner:    Mapped["User"]     = relationship("User",     back_populates="notes")     # noqa: F821
    syllabus: Mapped["Syllabus"] = relationship("Syllabus", back_populates="notes")     # noqa: F821
    chapter:  Mapped["Chapter"]  = relationship("Chapter",  back_populates="notes")     # noqa: F821
    guide:    Mapped["Guide"]    = relationship("Guide",    back_populates="note", uselist=False)  # noqa: F821
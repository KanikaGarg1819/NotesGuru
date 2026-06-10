from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Guide(Base):
    """
    A guide is the final AI-generated study output for a note.
    Stored as Markdown, rendered on the frontend.
    """
    __tablename__ = "guides"

    id:           Mapped[int]      = mapped_column(primary_key=True, index=True)
    title:        Mapped[str]      = mapped_column(String(255), nullable=False)
    content:      Mapped[str]      = mapped_column(Text,        nullable=False)  # Markdown
    chapter_name: Mapped[str]      = mapped_column(String(255), nullable=True)   # for display
    created_at:   Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Foreign keys
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    note_id:  Mapped[int] = mapped_column(ForeignKey("notes.id"), nullable=False, unique=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="guides")  # noqa: F821
    note:  Mapped["Note"] = relationship("Note", back_populates="guide")   # noqa: F821
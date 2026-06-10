from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Syllabus(Base):
    """
    A syllabus belongs to a user and has many chapters.
    e.g. 'Computer Networks — Semester 5'
    """
    __tablename__ = "syllabuses"

    id:         Mapped[int]      = mapped_column(primary_key=True, index=True)
    title:      Mapped[str]      = mapped_column(String(255), nullable=False)
    subject:    Mapped[str]      = mapped_column(String(255), nullable=False)
    semester:   Mapped[str]      = mapped_column(String(50),  nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Foreign key → User
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    owner:    Mapped["User"]          = relationship("User",    back_populates="syllabuses")  # noqa: F821
    chapters: Mapped[list["Chapter"]] = relationship("Chapter", back_populates="syllabus", cascade="all, delete-orphan")
    notes:    Mapped[list["Note"]]    = relationship("Note",    back_populates="syllabus")


class Chapter(Base):
    """
    A chapter is one topic/unit inside a syllabus.
    e.g. 'Unit 3: TCP/IP Model'
    The embedding is stored as a comma-separated float string — 
    we'll upgrade to pgvector later if needed.
    """
    __tablename__ = "chapters"

    id:          Mapped[int]  = mapped_column(primary_key=True, index=True)
    unit_number: Mapped[int]  = mapped_column(Integer, nullable=False)
    title:       Mapped[str]  = mapped_column(String(255), nullable=False)
    description: Mapped[str]  = mapped_column(Text, nullable=True)

    # Pre-computed embedding stored as text (comma-separated floats)
    embedding:   Mapped[str]  = mapped_column(Text, nullable=True)

    # Foreign key → Syllabus
    syllabus_id: Mapped[int]  = mapped_column(ForeignKey("syllabuses.id"), nullable=False)

    # Relationships
    syllabus: Mapped["Syllabus"] = relationship("Syllabus", back_populates="chapters")
    notes:    Mapped[list["Note"]] = relationship("Note",   back_populates="chapter")
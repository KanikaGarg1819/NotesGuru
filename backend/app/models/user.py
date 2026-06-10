from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id:         Mapped[int]      = mapped_column(primary_key=True, index=True)
    email:      Mapped[str]      = mapped_column(String(255), unique=True, index=True, nullable=False)
    username:   Mapped[str]      = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active:  Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    syllabuses: Mapped[list["Syllabus"]] = relationship("Syllabus", back_populates="owner")  # noqa: F821
    notes:      Mapped[list["Note"]]     = relationship("Note",     back_populates="owner")  # noqa: F821
    guides:     Mapped[list["Guide"]]    = relationship("Guide",    back_populates="owner")  # noqa: F821
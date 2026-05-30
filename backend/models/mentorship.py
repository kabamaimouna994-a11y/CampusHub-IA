from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, ForeignKey, DateTime, Text, Float, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def _now_utc():
    return datetime.now(timezone.utc)


class Mentorship(Base):
    __tablename__ = "mentorships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    mentee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="active")
    goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Notation du mentor par l'étudiant
    mentee_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mentee_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    mentor: Mapped["User"] = relationship(
        "User",
        foreign_keys=[mentor_id],
        back_populates="mentorships_as_mentor"
    )
    mentee: Mapped["User"] = relationship(
        "User",
        foreign_keys=[mentee_id],
        back_populates="mentorships_as_mentee"
    )
    sessions: Mapped[List["MentoringSession"]] = relationship(
        "MentoringSession",
        foreign_keys="MentoringSession.mentorship_id",
        back_populates="mentorship",
        cascade="all, delete-orphan"
    )
    messages: Mapped[List["MentorMessage"]] = relationship(
        "MentorMessage",
        foreign_keys="MentorMessage.mentorship_id",
        back_populates="mentorship",
        cascade="all, delete-orphan"
    )


class MentoringSession(Base):
    __tablename__ = "mentoring_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mentorship_id: Mapped[int] = mapped_column(ForeignKey("mentorships.id", ondelete="CASCADE"), index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, default=60)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="scheduled")

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mentor_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mentee_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mentor_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mentee_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    mentorship: Mapped["Mentorship"] = relationship(
        "Mentorship",
        foreign_keys=[mentorship_id],
        back_populates="sessions"
    )


class MentorMessage(Base):
    __tablename__ = "mentor_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mentorship_id: Mapped[int] = mapped_column(ForeignKey("mentorships.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)

    mentorship: Mapped["Mentorship"] = relationship(
        "Mentorship",
        foreign_keys=[mentorship_id],
        back_populates="messages"
    )

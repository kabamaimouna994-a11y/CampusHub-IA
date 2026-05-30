from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, ForeignKey, Boolean, DateTime, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=50)

    club_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clubs.id"), nullable=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    skill_tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    club: Mapped[Optional["Club"]] = relationship(
        "Club",
        foreign_keys=[club_id],
        back_populates="events"
    )
    registrations: Mapped[List["EventRegistration"]] = relationship(
        "EventRegistration",
        foreign_keys="EventRegistration.event_id",
        back_populates="event",
        cascade="all, delete-orphan"
    )

    @property
    def confirmed_registrations_count(self) -> int:
        return len([r for r in self.registrations if r.status == "confirmed"])

    @property
    def fill_rate(self) -> float:
        if self.capacity == 0:
            return 0.0
        return self.confirmed_registrations_count / self.capacity

    @property
    def available_spots(self) -> int:
        return max(0, self.capacity - self.confirmed_registrations_count)


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    status: Mapped[str] = mapped_column(String(50), default="confirmed")

    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    feedback_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    event: Mapped["Event"] = relationship(
        "Event",
        foreign_keys=[event_id],
        back_populates="registrations"
    )
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="event_registrations"
    )
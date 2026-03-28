import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ── User ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)

    # Resy credentials — stored encrypted (Fernet), nullable until user sets them
    resy_email_enc: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    resy_password_enc: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    resy_api_key_enc: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    hitlist: Mapped[List["HitlistRestaurant"]] = relationship(
        "HitlistRestaurant", back_populates="user", cascade="all, delete-orphan"
    )
    dates: Mapped[List["DateEvent"]] = relationship(
        "DateEvent", back_populates="user", cascade="all, delete-orphan"
    )


# ── Hitlist ───────────────────────────────────────────────────────────────────

class HitlistRestaurant(Base):
    __tablename__ = "hitlist_restaurants"
    __table_args__ = (
        UniqueConstraint("venue_id", "user_id", name="uq_hitlist_venue_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    venue_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String, default="")
    cuisine: Mapped[str] = mapped_column(String, default="")
    resy_url_token: Mapped[str] = mapped_column(String, default="")
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="hitlist")

    dates: Mapped[List["DateEvent"]] = relationship(
        "DateEvent", back_populates="restaurant", cascade="all, delete-orphan"
    )


# ── Date Events ───────────────────────────────────────────────────────────────

class DateStatus(str, enum.Enum):
    draft = "draft"          # created, not yet monitoring
    monitoring = "monitoring"  # actively polling for availability
    booked = "booked"        # reservation successfully made
    failed = "failed"        # window passed without booking
    cancelled = "cancelled"  # user cancelled


class DateEvent(Base):
    __tablename__ = "date_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    restaurant_id: Mapped[int] = mapped_column(Integer, ForeignKey("hitlist_restaurants.id"))

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="dates")

    # Desired booking window
    desired_date_start: Mapped[str] = mapped_column(String)   # YYYY-MM-DD
    desired_date_end: Mapped[str] = mapped_column(String)     # YYYY-MM-DD
    desired_time_start: Mapped[str] = mapped_column(String)   # HH:MM (24h)
    desired_time_end: Mapped[str] = mapped_column(String)     # HH:MM (24h)
    party_size: Mapped[int] = mapped_column(Integer, default=2)
    one_and_done: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[DateStatus] = mapped_column(
        Enum(DateStatus), default=DateStatus.draft
    )

    # Set after successful booking
    reservation_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    booked_slot: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    booked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    resy_notify_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    notes: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    restaurant: Mapped["HitlistRestaurant"] = relationship(
        "HitlistRestaurant", back_populates="dates"
    )

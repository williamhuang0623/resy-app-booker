import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class DateStatus(str, enum.Enum):
    draft = "draft"          # created, not yet monitoring
    monitoring = "monitoring"  # actively polling for availability
    booked = "booked"        # reservation successfully made
    failed = "failed"        # window passed without booking
    cancelled = "cancelled"  # user cancelled


class HitlistRestaurant(Base):
    __tablename__ = "hitlist_restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    venue_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String, default="")
    cuisine: Mapped[str] = mapped_column(String, default="")
    resy_url_token: Mapped[str] = mapped_column(String, default="")
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    dates: Mapped[List["DateEvent"]] = relationship(
        "DateEvent", back_populates="restaurant", cascade="all, delete-orphan"
    )


class DateEvent(Base):
    __tablename__ = "date_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    restaurant_id: Mapped[int] = mapped_column(Integer, ForeignKey("hitlist_restaurants.id"))

    # Desired booking window
    desired_date_start: Mapped[str] = mapped_column(String)   # YYYY-MM-DD
    desired_date_end: Mapped[str] = mapped_column(String)     # YYYY-MM-DD
    desired_time_start: Mapped[str] = mapped_column(String)   # HH:MM (24h)
    desired_time_end: Mapped[str] = mapped_column(String)     # HH:MM (24h)
    party_size: Mapped[int] = mapped_column(Integer, default=2)

    status: Mapped[DateStatus] = mapped_column(
        Enum(DateStatus), default=DateStatus.draft
    )

    # Set after successful booking
    reservation_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    booked_slot: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # ISO datetime
    booked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Optional Resy notify token (from Resy's built-in notify feature)
    resy_notify_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    notes: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    restaurant: Mapped["HitlistRestaurant"] = relationship(
        "HitlistRestaurant", back_populates="dates"
    )

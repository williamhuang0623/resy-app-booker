from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models import DateStatus


# ── Hitlist ──────────────────────────────────────────────────────────────────

class HitlistRestaurantCreate(BaseModel):
    venue_id: str
    name: str
    location: str = ""
    cuisine: str = ""
    resy_url_token: str = ""


class HitlistRestaurantOut(BaseModel):
    id: int
    venue_id: str
    name: str
    location: str
    cuisine: str
    resy_url_token: str
    added_at: datetime

    model_config = {"from_attributes": True}


# ── Date Events ───────────────────────────────────────────────────────────────

class DateEventCreate(BaseModel):
    restaurant_id: int
    desired_date_start: str   # YYYY-MM-DD
    desired_date_end: str     # YYYY-MM-DD
    desired_time_start: str   # HH:MM
    desired_time_end: str     # HH:MM
    party_size: int = 2
    one_and_done: bool = False
    notes: str = ""


class DateEventOut(BaseModel):
    id: int
    restaurant_id: int
    restaurant: HitlistRestaurantOut
    desired_date_start: str
    desired_date_end: str
    desired_time_start: str
    desired_time_end: str
    party_size: int
    one_and_done: bool
    status: DateStatus
    reservation_id: Optional[str]
    booked_slot: Optional[str]
    booked_at: Optional[datetime]
    resy_notify_id: Optional[str]
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Restaurant Search ─────────────────────────────────────────────────────────

class VenueResult(BaseModel):
    venue_id: str
    name: str
    location: str
    cuisine: str
    resy_url_token: str


class VenueSearchPage(BaseModel):
    results: list[VenueResult]
    page: int
    total_pages: int
    total: int


# ── Slot ─────────────────────────────────────────────────────────────────────

class SlotResult(BaseModel):
    config_id: str
    date: str
    time_slot: str
    party_size: int
    type: str


# ── Auth status ───────────────────────────────────────────────────────────────

class AuthStatus(BaseModel):
    authenticated: bool
    email: Optional[str] = None
    payment_method_count: int = 0

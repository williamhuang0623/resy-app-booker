"""
Resy API client.

Uses Resy's unofficial API. All endpoints are HTTPS and require:
  - Authorization: ResyAPI api_key="<key>"
  - X-Resy-Auth-Token: <user token> (for authenticated requests)
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

RESY_BASE = "https://api.resy.com"
RESY_HEADERS = {
    "Authorization": f'ResyAPI api_key="{settings.resy_api_key}"',
    "Origin": "https://resy.com",
    "Referer": "https://resy.com/",
    "User-Agent": "Mozilla/5.0 (compatible; ResyBooker/1.0)",
    "Content-Type": "application/x-www-form-urlencoded",
}


@dataclass
class ResyAuthState:
    token: str = ""
    payment_method_id: Optional[int] = None
    email: str = ""
    _payment_methods: list[dict] = field(default_factory=list)

    @property
    def is_authenticated(self) -> bool:
        return bool(self.token)

    def headers(self) -> dict[str, str]:
        return {**RESY_HEADERS, "X-Resy-Auth-Token": self.token}


# Module-level auth state — shared across the app lifetime
_auth = ResyAuthState()


def get_auth_state() -> ResyAuthState:
    return _auth


# ── Authentication ────────────────────────────────────────────────────────────

async def login(email: str, password: str) -> ResyAuthState:
    """Authenticate with Resy and store the auth token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{RESY_BASE}/3/auth/password",
            headers=RESY_HEADERS,
            data={"email": email, "password": password},
        )
        resp.raise_for_status()
        data = resp.json()

    _auth.token = data.get("token", "")
    _auth.email = email
    _auth._payment_methods = data.get("payment_methods", [])
    if _auth._payment_methods:
        _auth.payment_method_id = _auth._payment_methods[0].get("id")

    logger.info("Resy login successful for %s", email)
    return _auth


async def ensure_authenticated() -> ResyAuthState:
    """Login if we don't have a token yet."""
    if not _auth.is_authenticated and settings.resy_email and settings.resy_password:
        await login(settings.resy_email, settings.resy_password)
    return _auth


# ── Venue Search ──────────────────────────────────────────────────────────────

async def search_venues(query: str, lat: float = 40.7128, lon: float = -74.0060) -> list[dict]:
    """Search Resy venues by name. Defaults to NYC coordinates."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{RESY_BASE}/3/venuesearch/search",
            headers=RESY_HEADERS,
            data={
                "struct_data": json.dumps({
                    "query": query,
                    "geo": {"lat": lat, "lng": lon},
                    "per_page": 10,
                }),
            },
        )
        resp.raise_for_status()
        data = resp.json()

    hits: list[dict[str, Any]] = data.get("search", {}).get("hits", [])
    results = []
    for hit in hits:
        venue = hit.get("venue", {})
        locality = venue.get("location", {}).get("locality", "")
        region = venue.get("location", {}).get("region", "")
        results.append(
            {
                "venue_id": str(venue.get("id", {}).get("resy", "")),
                "name": venue.get("name", ""),
                "location": f"{locality}, {region}".strip(", "),
                "cuisine": ", ".join(
                    c.get("name", "") for c in venue.get("cuisine", [])
                ),
                "resy_url_token": venue.get("url_token", ""),
            }
        )
    return results


# ── Slot Discovery ────────────────────────────────────────────────────────────

async def find_slots(
    venue_id: str,
    day: str,  # YYYY-MM-DD
    party_size: int,
    time_start: str = "00:00",
    time_end: str = "23:59",
) -> list[dict]:
    """
    Find available reservation slots for a venue on a given day.
    Returns slots filtered to the desired time window.
    """
    auth = await ensure_authenticated()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{RESY_BASE}/4/find",
            headers=auth.headers() if auth.is_authenticated else RESY_HEADERS,
            params={
                "lat": 0,
                "long": 0,
                "day": day,
                "party_size": party_size,
                "venue_id": venue_id,
            },
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()

    slots = []
    for venue_data in data.get("results", {}).get("venues", []):
        for slot in venue_data.get("slots", []):
            date_info = slot.get("date", {})
            slot_start = date_info.get("start", "")  # e.g. "2024-01-15 19:00:00"
            if not slot_start:
                continue

            # Extract HH:MM for comparison
            slot_time = slot_start.split(" ")[-1][:5]
            if not (time_start <= slot_time <= time_end):
                continue

            config = slot.get("config", {})
            slots.append(
                {
                    "config_id": config.get("token", ""),
                    "date": day,
                    "time_slot": slot_start,
                    "party_size": party_size,
                    "type": config.get("type", ""),
                }
            )

    return slots


async def find_slots_in_range(
    venue_id: str,
    date_start: str,  # YYYY-MM-DD
    date_end: str,    # YYYY-MM-DD
    party_size: int,
    time_start: str = "00:00",
    time_end: str = "23:59",
) -> list[dict]:
    """Find slots across a date range."""
    from datetime import date, timedelta

    start = date.fromisoformat(date_start)
    end = date.fromisoformat(date_end)
    all_slots: list[dict] = []

    current = start
    while current <= end:
        day_str = current.isoformat()
        try:
            slots = await find_slots(venue_id, day_str, party_size, time_start, time_end)
            all_slots.extend(slots)
        except Exception as exc:
            logger.warning("Failed to fetch slots for %s on %s: %s", venue_id, day_str, exc)
        current += timedelta(days=1)

    return all_slots


# ── Booking ───────────────────────────────────────────────────────────────────

async def get_booking_token(config_id: str, day: str, party_size: int) -> Optional[str]:
    """Get a book_token for a specific slot (needed to complete booking)."""
    auth = await ensure_authenticated()
    if not auth.is_authenticated:
        logger.error("Cannot get booking token: not authenticated")
        return None

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{RESY_BASE}/3/details",
            headers=auth.headers(),
            data={
                "commit": 1,
                "config_id": config_id,
                "day": day,
                "party_size": party_size,
            },
        )
        if resp.status_code != 200:
            logger.warning("details endpoint returned %s", resp.status_code)
            return None
        data = resp.json()

    return data.get("book_token", {}).get("value")


async def book_slot(config_id: str, day: str, party_size: int) -> Optional[dict]:
    """
    Book a slot. Returns booking confirmation data or None on failure.
    """
    auth = await ensure_authenticated()
    if not auth.is_authenticated:
        logger.error("Cannot book: not authenticated")
        return None
    if not auth.payment_method_id:
        logger.error("Cannot book: no payment method on file")
        return None

    book_token = await get_booking_token(config_id, day, party_size)
    if not book_token:
        logger.error("Failed to obtain book_token for config_id=%s", config_id)
        return None

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{RESY_BASE}/3/book",
            headers=auth.headers(),
            data={
                "book_token": book_token,
                "struct_payment_method": f'{{"id":{auth.payment_method_id}}}',
                "source_id": "resy.com-venue-details",
            },
        )
        if resp.status_code != 201:
            logger.warning("book returned %s: %s", resp.status_code, resp.text)
            return None
        return resp.json()


# ── Resy Notify ───────────────────────────────────────────────────────────────

async def set_notify(venue_id: str, party_size: int, day: str) -> Optional[str]:
    """
    Register Resy's native notify for a venue/date/party_size.
    Returns the notify ID or None.
    """
    auth = await ensure_authenticated()
    if not auth.is_authenticated:
        return None

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{RESY_BASE}/3/user/notify",
            headers=auth.headers(),
            data={
                "venue_id": venue_id,
                "notify_party_size": party_size,
                "notify_date": day,
            },
        )
        if resp.status_code not in (200, 201):
            logger.warning("notify returned %s", resp.status_code)
            return None
        data = resp.json()

    return str(data.get("id", ""))


async def remove_notify(notify_id: str) -> bool:
    """Cancel a Resy notify subscription."""
    auth = await ensure_authenticated()
    if not auth.is_authenticated:
        return False

    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{RESY_BASE}/3/user/notify/{notify_id}",
            headers=auth.headers(),
        )
    return resp.status_code in (200, 204)

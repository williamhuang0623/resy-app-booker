"""
Resy API client.

Uses Resy's unofficial API. All endpoints are HTTPS and require:
  - Authorization: ResyAPI api_key="<key>"
  - X-Resy-Auth-Token: <user token> (for authenticated requests)

`ResyClient` holds per-user credentials and auth state.
Module-level `search_venues()` uses the public Resy web key (no auth needed).
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

RESY_BASE = "https://api.resy.com"
# Resy's public web-app key — same for all users, not a secret
_PUBLIC_API_KEY = "VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"


def _base_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f'ResyAPI api_key="{api_key}"',
        "Origin": "https://resy.com",
        "Referer": "https://resy.com/",
        "User-Agent": "Mozilla/5.0 (compatible; ResyBooker/1.0)",
        "Content-Type": "application/x-www-form-urlencoded",
    }


# ── Per-user client ───────────────────────────────────────────────────────────

class ResyClient:
    """Holds credentials + auth state for a single Resy account."""

    def __init__(self, resy_email: str, resy_password: str, api_key: str = _PUBLIC_API_KEY):
        self.resy_email = resy_email
        self.resy_password = resy_password
        self.api_key = api_key
        self._auth_token: str = ""
        self._payment_method_id: Optional[int] = None
        self._payment_methods: list[dict] = []

    @property
    def is_authenticated(self) -> bool:
        return bool(self._auth_token)

    def _headers(self) -> dict[str, str]:
        h = _base_headers(self.api_key)
        if self._auth_token:
            h["X-Resy-Auth-Token"] = self._auth_token
        return h

    async def login(self) -> bool:
        """Authenticate with Resy. Returns True on success."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{RESY_BASE}/3/auth/password",
                headers=_base_headers(self.api_key),
                data={"email": self.resy_email, "password": self.resy_password},
            )
            if resp.status_code != 200:
                logger.warning(
                    "Resy login failed for %s: %s %s",
                    self.resy_email,
                    resp.status_code,
                    resp.text[:200],
                )
                return False
            data = resp.json()

        self._auth_token = data.get("token", "")
        self._payment_methods = data.get("payment_methods", [])
        if self._payment_methods:
            self._payment_method_id = self._payment_methods[0].get("id")

        logger.info("Resy login OK for %s", self.resy_email)
        return True

    async def ensure_authenticated(self) -> bool:
        if not self.is_authenticated:
            return await self.login()
        return True

    # ── Slot Discovery ────────────────────────────────────────────────────────

    async def find_slots(
        self,
        venue_id: str,
        day: str,
        party_size: int,
        time_start: str = "00:00",
        time_end: str = "23:59",
    ) -> list[dict]:
        await self.ensure_authenticated()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{RESY_BASE}/4/find",
                headers=self._headers(),
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
                slot_start = date_info.get("start", "")
                if not slot_start:
                    continue
                slot_time = slot_start.split(" ")[-1][:5]
                if not (time_start <= slot_time <= time_end):
                    continue
                config = slot.get("config", {})
                slots.append({
                    "config_id": config.get("token", ""),
                    "date": day,
                    "time_slot": slot_start,
                    "party_size": party_size,
                    "type": config.get("type", ""),
                })
        return slots

    async def find_slots_in_range(
        self,
        venue_id: str,
        date_start: str,
        date_end: str,
        party_size: int,
        time_start: str = "00:00",
        time_end: str = "23:59",
    ) -> list[dict]:
        from datetime import date, timedelta

        start = date.fromisoformat(date_start)
        end = date.fromisoformat(date_end)
        all_slots: list[dict] = []

        current = start
        while current <= end:
            day_str = current.isoformat()
            try:
                slots = await self.find_slots(venue_id, day_str, party_size, time_start, time_end)
                all_slots.extend(slots)
            except Exception as exc:
                logger.warning("Failed to fetch slots for %s on %s: %s", venue_id, day_str, exc)
            current += timedelta(days=1)

        return all_slots

    # ── Booking ───────────────────────────────────────────────────────────────

    async def get_booking_token(self, config_id: str, day: str, party_size: int) -> Optional[str]:
        if not self.is_authenticated:
            return None
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{RESY_BASE}/3/details",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"commit": 1, "config_id": config_id, "day": day, "party_size": party_size},
            )
            if resp.status_code not in (200, 201):
                logger.warning("details returned %s", resp.status_code)
                return None
            data = resp.json()
        return data.get("book_token", {}).get("value")

    async def book_slot(self, config_id: str, day: str, party_size: int) -> Optional[dict]:
        if not self.is_authenticated:
            logger.error("Cannot book: not authenticated (%s)", self.resy_email)
            return None
        if not self._payment_method_id:
            logger.error("Cannot book: no payment method (%s)", self.resy_email)
            return None

        book_token = await self.get_booking_token(config_id, day, party_size)
        if not book_token:
            return None

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{RESY_BASE}/3/book",
                headers=self._headers(),
                data={
                    "book_token": book_token,
                    "struct_payment_method": f'{{"id":{self._payment_method_id}}}',
                    "source_id": "resy.com-venue-details",
                },
            )
            if resp.status_code != 201:
                logger.warning("book returned %s: %s", resp.status_code, resp.text)
                return None
            return resp.json()

    # ── Resy Notify ───────────────────────────────────────────────────────────

    async def set_notify(self, venue_id: str, party_size: int, day: str) -> Optional[str]:
        if not await self.ensure_authenticated():
            return None
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{RESY_BASE}/3/user/notify",
                headers=self._headers(),
                data={"venue_id": venue_id, "notify_party_size": party_size, "notify_date": day},
            )
            if resp.status_code not in (200, 201):
                return None
            data = resp.json()
        return str(data.get("id", ""))

    async def remove_notify(self, notify_id: str) -> bool:
        if not self.is_authenticated:
            return False
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{RESY_BASE}/3/user/notify/{notify_id}",
                headers=self._headers(),
            )
        return resp.status_code in (200, 204)


# ── Module-level helpers (no auth needed) ────────────────────────────────────

async def search_venues(query: str, page: int = 1) -> dict:
    """Search Resy venues by name. Uses public API key — no auth required."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{RESY_BASE}/3/venuesearch/search",
            headers=_base_headers(_PUBLIC_API_KEY),
            data={
                "struct_data": json.dumps({
                    "query": query,
                    "per_page": 10,
                    "page": page,
                }),
            },
        )
        resp.raise_for_status()
        data = resp.json()

    search = data.get("search", {})
    hits: list[dict[str, Any]] = search.get("hits", [])
    results = []
    for hit in hits:
        neighborhood = hit.get("neighborhood", "")
        locality = hit.get("locality", "")
        location = ", ".join(p for p in [neighborhood, locality] if p)
        results.append({
            "venue_id": str(hit.get("id", {}).get("resy", "")),
            "name": hit.get("name", ""),
            "location": location,
            "cuisine": ", ".join(hit.get("cuisine", [])),
            "resy_url_token": hit.get("url_slug", ""),
        })

    total = min(search.get("nbHits", len(results)), 100)
    total_pages = min(search.get("nbPages", 1), 10)
    return {
        "results": results,
        "page": search.get("page", page),
        "total_pages": total_pages,
        "total": total,
    }


# ── In-memory per-user client cache ──────────────────────────────────────────

_user_clients: dict[int, ResyClient] = {}


def get_client_for_user(
    user_id: int,
    resy_email: str,
    resy_password: str,
    api_key: str = _PUBLIC_API_KEY,
) -> ResyClient:
    """Return a cached ResyClient for a user, creating one if needed."""
    existing = _user_clients.get(user_id)
    if existing and existing.resy_email == resy_email:
        return existing
    client = ResyClient(resy_email, resy_password, api_key)
    _user_clients[user_id] = client
    return client


def invalidate_client(user_id: int) -> None:
    """Evict a cached client (call after credential update)."""
    _user_clients.pop(user_id, None)

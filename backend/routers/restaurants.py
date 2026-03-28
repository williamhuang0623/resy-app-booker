from fastapi import APIRouter, HTTPException, Query

from schemas import AuthStatus, SlotResult, VenueResult
from services import resy_client

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("/search", response_model=list[VenueResult])
async def search_restaurants(
    q: str = Query(..., description="Restaurant name to search"),
):
    """Search Resy for venues matching the query."""
    try:
        results = await resy_client.search_venues(q)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Resy search failed: {exc}") from exc
    return results


@router.get("/slots", response_model=list[SlotResult])
async def get_slots(
    venue_id: str,
    date: str = Query(..., description="YYYY-MM-DD"),
    party_size: int = Query(2),
    time_start: str = Query("00:00"),
    time_end: str = Query("23:59"),
):
    """Check live availability for a venue on a specific date."""
    try:
        slots = await resy_client.find_slots(
            venue_id=venue_id,
            day=date,
            party_size=party_size,
            time_start=time_start,
            time_end=time_end,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Resy slots failed: {exc}") from exc
    return slots


@router.get("/auth/status", response_model=AuthStatus)
async def auth_status():
    """Check whether the app is authenticated with Resy."""
    auth = resy_client.get_auth_state()
    return AuthStatus(
        authenticated=auth.is_authenticated,
        email=auth.email or None,
        payment_method_count=len(auth._payment_methods),
    )


@router.post("/auth/login", response_model=AuthStatus)
async def login(email: str, password: str):
    """Manually trigger Resy login (useful if env vars aren't set)."""
    try:
        auth = await resy_client.login(email, password)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Login failed: {exc}") from exc
    return AuthStatus(
        authenticated=auth.is_authenticated,
        email=auth.email,
        payment_method_count=len(auth._payment_methods),
    )

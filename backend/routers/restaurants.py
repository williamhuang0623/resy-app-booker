from fastapi import APIRouter, HTTPException, Query

from schemas import SlotResult, VenueResult, VenueSearchPage
from services import resy_client as rc

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("/search", response_model=VenueSearchPage)
async def search_restaurants(
    q: str = Query(..., description="Restaurant name to search"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
):
    """Search Resy for venues by name. No auth required."""
    try:
        return await rc.search_venues(q, page=page)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Resy search failed: {exc}") from exc


@router.get("/slots", response_model=list[SlotResult])
async def get_slots(
    venue_id: str,
    date: str = Query(..., description="YYYY-MM-DD"),
    party_size: int = Query(2),
    time_start: str = Query("00:00"),
    time_end: str = Query("23:59"),
):
    """Check live availability for a venue on a specific date."""
    # Use a temporary client with the public key for unauthenticated slot lookup
    client = rc.ResyClient("", "", rc._PUBLIC_API_KEY)
    try:
        slots = await client.find_slots(
            venue_id=venue_id,
            day=date,
            party_size=party_size,
            time_start=time_start,
            time_end=time_end,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Resy slots failed: {exc}") from exc
    return slots

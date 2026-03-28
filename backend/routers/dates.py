from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import DateEvent, DateStatus, HitlistRestaurant
from schemas import DateEventCreate, DateEventOut, DateEventUpdate
from services import resy_client

router = APIRouter(prefix="/dates", tags=["dates"])


@router.get("/", response_model=list[DateEventOut])
def list_dates(db: Session = Depends(get_db)):
    return (
        db.query(DateEvent)
        .order_by(DateEvent.created_at.desc())
        .all()
    )


@router.post("/", response_model=DateEventOut, status_code=201)
def create_date(payload: DateEventCreate, db: Session = Depends(get_db)):
    restaurant = db.get(HitlistRestaurant, payload.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found on hitlist")

    date_event = DateEvent(**payload.model_dump())
    db.add(date_event)
    db.commit()
    db.refresh(date_event)
    return date_event


@router.post("/{date_id}/monitor", response_model=DateEventOut)
async def start_monitoring(date_id: int, db: Session = Depends(get_db)):
    """
    Activate auto-booking for a Date.
    Also registers Resy's native notify as a secondary signal.
    """
    date_event = db.get(DateEvent, date_id)
    if not date_event:
        raise HTTPException(status_code=404, detail="Date not found")
    if date_event.status not in (DateStatus.draft, DateStatus.failed):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot start monitoring from status '{date_event.status}'",
        )

    # Register Resy notify for the start date
    try:
        notify_id = await resy_client.set_notify(
            venue_id=date_event.restaurant.venue_id,
            party_size=date_event.party_size,
            day=date_event.desired_date_start,
        )
        if notify_id:
            date_event.resy_notify_id = notify_id
    except Exception:
        pass  # notify is best-effort; don't block activation

    date_event.status = DateStatus.monitoring
    db.commit()
    db.refresh(date_event)
    return date_event


@router.post("/{date_id}/cancel", response_model=DateEventOut)
async def cancel_date(date_id: int, db: Session = Depends(get_db)):
    date_event = db.get(DateEvent, date_id)
    if not date_event:
        raise HTTPException(status_code=404, detail="Date not found")
    if date_event.status == DateStatus.booked:
        raise HTTPException(status_code=409, detail="Cannot cancel a booked reservation here")

    # Clean up Resy notify if registered
    if date_event.resy_notify_id:
        try:
            await resy_client.remove_notify(date_event.resy_notify_id)
        except Exception:
            pass

    date_event.status = DateStatus.cancelled
    db.commit()
    db.refresh(date_event)
    return date_event


@router.patch("/{date_id}", response_model=DateEventOut)
async def update_date(date_id: int, payload: DateEventUpdate, db: Session = Depends(get_db)):
    """
    Update a Date's details. If it was monitoring, it is restarted automatically.
    Booked Dates cannot be edited.
    """
    date_event = db.get(DateEvent, date_id)
    if not date_event:
        raise HTTPException(status_code=404, detail="Date not found")
    if date_event.status == DateStatus.booked:
        raise HTTPException(status_code=409, detail="Cannot edit a booked reservation")

    was_monitoring = date_event.status == DateStatus.monitoring

    for field, value in payload.model_dump().items():
        setattr(date_event, field, value)

    # Drop back to draft so the scheduler picks up new params cleanly
    date_event.status = DateStatus.draft
    date_event.resy_notify_id = None
    db.commit()

    # Restart monitoring if it was active before the edit
    if was_monitoring:
        try:
            notify_id = await resy_client.set_notify(
                venue_id=date_event.restaurant.venue_id,
                party_size=date_event.party_size,
                day=date_event.desired_date_start,
            )
            if notify_id:
                date_event.resy_notify_id = notify_id
        except Exception:
            pass
        date_event.status = DateStatus.monitoring
        db.commit()

    db.refresh(date_event)
    return date_event


@router.get("/{date_id}", response_model=DateEventOut)
def get_date(date_id: int, db: Session = Depends(get_db)):
    date_event = db.get(DateEvent, date_id)
    if not date_event:
        raise HTTPException(status_code=404, detail="Date not found")
    return date_event


@router.delete("/{date_id}", status_code=204)
async def delete_date(date_id: int, db: Session = Depends(get_db)):
    date_event = db.get(DateEvent, date_id)
    if not date_event:
        raise HTTPException(status_code=404, detail="Date not found")
    if date_event.resy_notify_id:
        try:
            await resy_client.remove_notify(date_event.resy_notify_id)
        except Exception:
            pass
    db.delete(date_event)
    db.commit()

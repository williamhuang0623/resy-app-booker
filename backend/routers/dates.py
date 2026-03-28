from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import DateEvent, DateStatus, HitlistRestaurant, User
from routers.auth import get_current_user
from schemas import DateEventCreate, DateEventOut, DateEventUpdate
from services import resy_client as rc
from services.security import safe_decrypt

router = APIRouter(prefix="/dates", tags=["dates"])


async def _get_notify_client(current_user: User):
    """Return a ResyClient for the current user, or None if credentials missing."""
    email = safe_decrypt(current_user.resy_email_enc)
    password = safe_decrypt(current_user.resy_password_enc)
    api_key = safe_decrypt(current_user.resy_api_key_enc) or rc._PUBLIC_API_KEY
    if not email or not password:
        return None
    return rc.get_client_for_user(current_user.id, email, password, api_key)


@router.get("/", response_model=list[DateEventOut])
def list_dates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(DateEvent)
        .filter(DateEvent.user_id == current_user.id)
        .order_by(DateEvent.created_at.desc())
        .all()
    )


@router.post("/", response_model=DateEventOut, status_code=201)
def create_date(
    payload: DateEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = (
        db.query(HitlistRestaurant)
        .filter(
            HitlistRestaurant.id == payload.restaurant_id,
            HitlistRestaurant.user_id == current_user.id,
        )
        .first()
    )
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found on hitlist")

    date_event = DateEvent(**payload.model_dump(), user_id=current_user.id)
    db.add(date_event)
    db.commit()
    db.refresh(date_event)
    return date_event


@router.post("/{date_id}/monitor", response_model=DateEventOut)
async def start_monitoring(
    date_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    date_event = (
        db.query(DateEvent)
        .filter(DateEvent.id == date_id, DateEvent.user_id == current_user.id)
        .first()
    )
    if not date_event:
        raise HTTPException(status_code=404, detail="Date not found")
    if date_event.status not in (DateStatus.draft, DateStatus.failed):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot start monitoring from status '{date_event.status}'",
        )

    client = await _get_notify_client(current_user)
    if client:
        try:
            notify_id = await client.set_notify(
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


@router.post("/{date_id}/cancel", response_model=DateEventOut)
async def cancel_date(
    date_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    date_event = (
        db.query(DateEvent)
        .filter(DateEvent.id == date_id, DateEvent.user_id == current_user.id)
        .first()
    )
    if not date_event:
        raise HTTPException(status_code=404, detail="Date not found")
    if date_event.status == DateStatus.booked:
        raise HTTPException(status_code=409, detail="Cannot cancel a booked reservation here")

    if date_event.resy_notify_id:
        client = await _get_notify_client(current_user)
        if client:
            try:
                await client.remove_notify(date_event.resy_notify_id)
            except Exception:
                pass

    date_event.status = DateStatus.cancelled
    db.commit()
    db.refresh(date_event)
    return date_event


@router.patch("/{date_id}", response_model=DateEventOut)
async def update_date(
    date_id: int,
    payload: DateEventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    date_event = (
        db.query(DateEvent)
        .filter(DateEvent.id == date_id, DateEvent.user_id == current_user.id)
        .first()
    )
    if not date_event:
        raise HTTPException(status_code=404, detail="Date not found")
    if date_event.status == DateStatus.booked:
        raise HTTPException(status_code=409, detail="Cannot edit a booked reservation")

    was_monitoring = date_event.status == DateStatus.monitoring

    for field, value in payload.model_dump().items():
        setattr(date_event, field, value)

    date_event.status = DateStatus.draft
    date_event.resy_notify_id = None
    db.commit()

    if was_monitoring:
        client = await _get_notify_client(current_user)
        if client:
            try:
                notify_id = await client.set_notify(
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
def get_date(
    date_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    date_event = (
        db.query(DateEvent)
        .filter(DateEvent.id == date_id, DateEvent.user_id == current_user.id)
        .first()
    )
    if not date_event:
        raise HTTPException(status_code=404, detail="Date not found")
    return date_event


@router.delete("/{date_id}", status_code=204)
async def delete_date(
    date_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    date_event = (
        db.query(DateEvent)
        .filter(DateEvent.id == date_id, DateEvent.user_id == current_user.id)
        .first()
    )
    if not date_event:
        raise HTTPException(status_code=404, detail="Date not found")
    if date_event.resy_notify_id:
        client = await _get_notify_client(current_user)
        if client:
            try:
                await client.remove_notify(date_event.resy_notify_id)
            except Exception:
                pass
    db.delete(date_event)
    db.commit()

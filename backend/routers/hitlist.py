from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import HitlistRestaurant, User
from routers.auth import get_current_user
from schemas import HitlistRestaurantCreate, HitlistRestaurantOut

router = APIRouter(prefix="/hitlist", tags=["hitlist"])


@router.get("/", response_model=list[HitlistRestaurantOut])
def list_hitlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(HitlistRestaurant)
        .filter(HitlistRestaurant.user_id == current_user.id)
        .order_by(HitlistRestaurant.added_at.desc())
        .all()
    )


@router.post("/", response_model=HitlistRestaurantOut, status_code=201)
def add_to_hitlist(
    payload: HitlistRestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(HitlistRestaurant)
        .filter(
            HitlistRestaurant.venue_id == payload.venue_id,
            HitlistRestaurant.user_id == current_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Restaurant already on hitlist")

    restaurant = HitlistRestaurant(**payload.model_dump(), user_id=current_user.id)
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.delete("/{restaurant_id}", status_code=204)
def remove_from_hitlist(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = (
        db.query(HitlistRestaurant)
        .filter(
            HitlistRestaurant.id == restaurant_id,
            HitlistRestaurant.user_id == current_user.id,
        )
        .first()
    )
    if not restaurant:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(restaurant)
    db.commit()

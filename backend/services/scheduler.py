"""
Background scheduler that polls Resy for available slots and auto-books
any DateEvent that is in 'monitoring' status.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
from models import DateEvent, DateStatus, User
from services import resy_client as rc
from services.security import safe_decrypt

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _get_client_for_event(db: Session, date_event: DateEvent):
    """
    Build/retrieve a ResyClient for the user who owns this DateEvent.
    Returns None if credentials are missing or the event has no user.
    """
    if not date_event.user_id:
        logger.warning("Date #%d has no user_id — skipping", date_event.id)
        return None

    user: User = db.get(User, date_event.user_id)
    if not user:
        logger.warning("User %d not found for Date #%d — skipping", date_event.user_id, date_event.id)
        return None

    resy_email = safe_decrypt(user.resy_email_enc)
    resy_password = safe_decrypt(user.resy_password_enc)
    api_key = safe_decrypt(user.resy_api_key_enc) or rc._PUBLIC_API_KEY

    if not resy_email or not resy_password:
        logger.warning(
            "User %d has no Resy credentials — skipping Date #%d", user.id, date_event.id
        )
        return None

    return rc.get_client_for_user(user.id, resy_email, resy_password, api_key)


async def _try_book_date(db: Session, date_event: DateEvent) -> bool:
    """
    Check for availability and attempt to book a single DateEvent.
    Returns True if booking succeeded.
    """
    client = _get_client_for_event(db, date_event)
    if not client:
        return False

    restaurant = date_event.restaurant
    logger.info(
        "Polling %s (Date #%d) for %s–%s, %s–%s, party=%d",
        restaurant.name,
        date_event.id,
        date_event.desired_date_start,
        date_event.desired_date_end,
        date_event.desired_time_start,
        date_event.desired_time_end,
        date_event.party_size,
    )

    slots = await client.find_slots_in_range(
        venue_id=restaurant.venue_id,
        date_start=date_event.desired_date_start,
        date_end=date_event.desired_date_end,
        party_size=date_event.party_size,
        time_start=date_event.desired_time_start,
        time_end=date_event.desired_time_end,
    )

    if not slots:
        logger.debug("No slots found for Date #%d", date_event.id)
        return False

    slots.sort(key=lambda s: s["time_slot"])
    chosen = slots[0]
    logger.info(
        "Found slot for Date #%d: %s config_id=%s",
        date_event.id,
        chosen["time_slot"],
        chosen["config_id"],
    )

    day = chosen["date"]
    booking = await client.book_slot(
        config_id=chosen["config_id"],
        day=day,
        party_size=date_event.party_size,
    )

    if not booking:
        logger.warning("Booking attempt failed for Date #%d", date_event.id)
        return False

    date_event.status = DateStatus.booked
    date_event.reservation_id = str(
        booking.get("reservation_id") or booking.get("resy_token") or ""
    )
    date_event.booked_slot = chosen["time_slot"]
    date_event.booked_at = datetime.now(timezone.utc)

    # One-and-done: cancel every other monitoring Date for the same user
    if date_event.one_and_done:
        others = (
            db.query(DateEvent)
            .filter(
                DateEvent.status == DateStatus.monitoring,
                DateEvent.user_id == date_event.user_id,
                DateEvent.id != date_event.id,
            )
            .all()
        )
        for other in others:
            other.status = DateStatus.cancelled
            logger.info(
                "One-and-done: cancelled Date #%d (%s) after booking Date #%d",
                other.id,
                other.restaurant.name,
                date_event.id,
            )

    db.commit()

    logger.info(
        "Successfully booked %s for Date #%d at %s",
        restaurant.name,
        date_event.id,
        chosen["time_slot"],
    )
    return True


async def poll_and_book():
    """Main polling job — runs on every scheduler tick."""
    db: Session = SessionLocal()
    try:
        monitoring = (
            db.query(DateEvent)
            .filter(DateEvent.status == DateStatus.monitoring)
            .all()
        )

        if not monitoring:
            return

        logger.info("Scheduler tick: checking %d active Date(s)", len(monitoring))
        today = datetime.now(timezone.utc).date().isoformat()

        for date_event in monitoring:
            if date_event.desired_date_end < today:
                date_event.status = DateStatus.failed
                db.commit()
                logger.info(
                    "Date #%d marked failed: window %s–%s is past",
                    date_event.id,
                    date_event.desired_date_start,
                    date_event.desired_date_end,
                )
                continue

            try:
                await _try_book_date(db, date_event)
            except Exception as exc:
                logger.error(
                    "Unexpected error while processing Date #%d: %s",
                    date_event.id,
                    exc,
                    exc_info=True,
                )
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        poll_and_book,
        "interval",
        seconds=settings.poll_interval_seconds,
        id="poll_and_book",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — polling every %ds", settings.poll_interval_seconds)


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)

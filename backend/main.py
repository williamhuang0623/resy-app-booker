import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import Base, engine
from routers import dates, hitlist, restaurants
from services import resy_client
from services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resy Date Booker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hitlist.router, prefix="/api")
app.include_router(dates.router, prefix="/api")
app.include_router(restaurants.router, prefix="/api")


@app.on_event("startup")
async def startup():
    # Auto-login if credentials are configured
    if settings.resy_email and settings.resy_password:
        try:
            await resy_client.login(settings.resy_email, settings.resy_password)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Auto-login failed: %s", exc)

    start_scheduler()


@app.on_event("shutdown")
async def shutdown():
    stop_scheduler()


@app.get("/api/health")
def health():
    return {"status": "ok"}

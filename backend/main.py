import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import Base, engine
from routers import dates, hitlist, restaurants
from routers.auth import router as auth_router
from services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

# Create tables (new tables only — existing tables are not modified)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resy Date Booker", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(hitlist.router, prefix="/api")
app.include_router(dates.router, prefix="/api")
app.include_router(restaurants.router, prefix="/api")


@app.on_event("startup")
async def startup():
    start_scheduler()


@app.on_event("shutdown")
async def shutdown():
    stop_scheduler()


@app.get("/api/health")
def health():
    return {"status": "ok"}

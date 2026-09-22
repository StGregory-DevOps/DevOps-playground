from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import checks, health, monitors

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PulseCheck API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(monitors.router)
app.include_router(checks.router)

"""
Narmada Jal Nyay AI – FastAPI Application Entry Point
"""
import os
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .database.db import init_db
from .database.seed import seed
from .api import canal, farmers, schedule, complaints, dashboard, alerts, auth, simulate

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    try:
        await seed()
    except Exception as e:
        # Seed may fail on re-run (duplicate unique keys) – that's OK
        print(f"[Seed] Skipped or partial: {e}")
    yield
    # Shutdown (nothing to clean up)


app = FastAPI(
    title="Narmada Jal Nyay AI",
    description="Agentic AI-powered canal water distribution equity system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router,     prefix="/api/auth",     tags=["auth"])
app.include_router(canal.router,    prefix="/api/canal",    tags=["canal"])
app.include_router(farmers.router,  prefix="/api/farmers",  tags=["farmers"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["schedule"])
app.include_router(complaints.router, prefix="/api/complaints", tags=["complaints"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(alerts.router,   prefix="/api/alerts",   tags=["alerts"])
app.include_router(simulate.router, prefix="/api/simulate", tags=["simulate"])


@app.get("/", tags=["root"])
async def root():
    return {
        "name": "Narmada Jal Nyay AI",
        "tagline": "Fair Water for Every Farmer",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", tags=["root"])
async def health():
    return {"status": "healthy"}

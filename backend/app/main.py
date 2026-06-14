from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import admins, agent, audit, borrowing, conversations, copies, export, literature, models, notifications, readers, reservations, statistics, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

app.include_router(admins.router)
app.include_router(agent.router)
app.include_router(audit.router)
app.include_router(borrowing.router)
app.include_router(conversations.router)
app.include_router(copies.router)
app.include_router(export.router)
app.include_router(literature.router)
app.include_router(models.router)
app.include_router(notifications.router)
app.include_router(readers.router)
app.include_router(reservations.router)
app.include_router(statistics.router)
app.include_router(system.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.app_version}

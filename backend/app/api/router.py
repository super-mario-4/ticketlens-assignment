from fastapi import APIRouter

from app.api.routes import auth, health, imports, meta, stats, tickets

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(imports.router)
api_router.include_router(meta.router)
api_router.include_router(stats.router)
api_router.include_router(tickets.router)

from fastapi import APIRouter

from gov_mine.modules.health.router import router as health_router
from gov_mine.modules.ingest.router import router as ingest_router
from gov_mine.modules.runs.router import router as runs_router

router = APIRouter()
router.include_router(health_router)
router.include_router(runs_router)
router.include_router(ingest_router)

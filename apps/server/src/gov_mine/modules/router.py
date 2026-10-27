from fastapi import APIRouter

from gov_mine.modules.health.router import router as health_router

router = APIRouter()
router.include_router(health_router)

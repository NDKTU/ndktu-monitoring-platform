from fastapi import APIRouter
from app.modules.camera.router import router as camera_router
from app.modules.user.router import router as user_router
from app.modules.user_event.router import router as user_event_router

router = APIRouter()

router.include_router(camera_router)
router.include_router(user_router)
router.include_router(user_event_router)
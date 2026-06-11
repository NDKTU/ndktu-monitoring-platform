from app.core.config import settings

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uvicorn

from app.modules.camera.tasks import close_open_events_at_midnight
from app.modules.auth.init_rbac import init_rbac

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize RBAC
    await init_rbac(app)
    
    # Start active camera streams
    from app.modules.camera.stream import camera_manager
    await camera_manager.start_active_cameras()
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(close_open_events_at_midnight, 'cron', hour=0, minute=0)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

from app.modules.router import router as api_router

app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.app.host,
        port=settings.app.port,
    )

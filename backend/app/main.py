from app.core.config import settings

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uvicorn

from app.modules.camera.tasks import close_open_events_at_midnight

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(close_open_events_at_midnight, 'cron', hour=0, minute=0)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

from app.modules.camera.router import router as camera_router
from app.modules.user.router import router as user_router

app.include_router(camera_router)
app.include_router(user_router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.app.host,
        port=settings.app.port,
    )

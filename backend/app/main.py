from app.core.config import settings

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn


app = FastAPI()

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")




if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.app.host,
        port=settings.app.port,
    )

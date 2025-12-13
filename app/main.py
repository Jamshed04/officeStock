from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api import router as api_router
from core.config import settings
from core.models import db_helper


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
    await db_helper.dispose()

main_app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

origins = ["*"]

main_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # или ["*"] для всех
    allow_credentials=True,
    allow_methods=["*"],    # GET, POST, PUT, DELETE и т.д.
    allow_headers=["*"],    # все заголовки
)

main_app.include_router(
    api_router,
)

if __name__ == '__main__':
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True
    )

from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI
import uvicorn
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api import router as api_router
from core.config import settings
from core.models import db_helper
from crud.writeoff import process_writeoffs

logger = logging.getLogger(__name__)


async def writeoff_worker():
    """
    Воркер для автоматического списания товаров.
    Запускается сразу при старте, затем каждые 5 часов.
    """
    # Запускаем сразу при старте
    try:
        async with db_helper.session_factory() as session:
            try:
                results = await process_writeoffs(session)
                logger.info(
                    f"Write-off worker (startup) completed: "
                    f"processed={results['processed']}, "
                    f"written_off={results['written_off']}, "
                    f"deactivated={results['deactivated']}, "
                    f"errors={len(results['errors'])}"
                )
                if results['errors']:
                    logger.error(f"Write-off errors: {results['errors']}")
            except Exception as e:
                logger.error(f"Error in write-off worker (startup): {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in write-off worker (startup): {str(e)}", exc_info=True)

    # Затем запускаем каждые 5 часов
    while True:
        try:
            await asyncio.sleep(5 * 60 * 60)  # 5 часов в секундах

            # Создаем сессию БД для воркера
            async with db_helper.session_factory() as session:
                try:
                    results = await process_writeoffs(session)
                    logger.info(
                        f"Write-off worker completed: "
                        f"processed={results['processed']}, "
                        f"written_off={results['written_off']}, "
                        f"deactivated={results['deactivated']}, "
                        f"errors={len(results['errors'])}"
                    )
                    if results['errors']:
                        logger.error(f"Write-off errors: {results['errors']}")
                except Exception as e:
                    logger.error(f"Error in write-off worker: {str(e)}", exc_info=True)
        except asyncio.CancelledError:
            logger.info("Write-off worker cancelled")
            break
        except Exception as e:
            logger.error(f"Unexpected error in write-off worker: {str(e)}", exc_info=True)
            await asyncio.sleep(60)  # Ждем минуту перед повтором при ошибке


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    # Запускаем воркер списания в фоне
    worker_task = asyncio.create_task(writeoff_worker())
    logger.info("Write-off worker started")

    yield

    # shutdown
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
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

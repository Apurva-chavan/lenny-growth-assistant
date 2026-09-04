from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import get_settings
from app.logging_config import setup_logging, get_logger
from app.db.database import init_db
from app.knowledge.retriever import build_index
from app.api import sessions, messages, health

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup_begin")
    try:
        await init_db()
    except Exception as e:
        logger.error("db_init_failed", error=str(e))

    try:
        build_index()
    except Exception as e:
        logger.error("index_build_failed", error=str(e))

    logger.info("startup_complete")
    yield
    logger.info("shutdown")


settings = get_settings()

app = FastAPI(
    title="Lenny Growth Assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=str(request.url), error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router)
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")

from fastapi import APIRouter
from app.api.schemas import HealthResponse
from app.agent.llm_client import check_ollama_health
from app.knowledge.retriever import get_index_stats
from app.config import get_settings
from app.db.database import get_engine
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    settings = get_settings()
    stats = get_index_stats()

    # DB check
    db_ok = False
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    ollama_ok = None
    if settings.llm_provider == "ollama":
        ollama_ok = await check_ollama_health(settings.ollama_base_url)

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        llm_provider=settings.llm_provider,
        ollama_available=ollama_ok,
        index_chunks=stats["chunks"],
        index_ready=stats["index_ready"],
        db_connected=db_ok,
    )

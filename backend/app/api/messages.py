from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db import crud
from app.api.schemas import MessageCreate, MessageResponse, ChatResponse, ArtifactResponse, SourceRef
from app.agent.agent import run_agent
from app.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["messages"])


@router.get("", response_model=list[MessageResponse])
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await crud.get_messages(db, session_id)


@router.post("", response_model=ChatResponse, status_code=201)
async def send_message(session_id: str, body: MessageCreate, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Persist user message
    await crud.add_message(db, session_id, "user", body.content)

    # Build history for agent
    db_messages = await crud.get_messages(db, session_id)
    history = [{"role": m.role, "content": m.content} for m in db_messages[:-1]]  # exclude just-added user msg

    try:
        result = await run_agent(body.content, history, session_id)
    except RuntimeError as e:
        logger.error("agent_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("agent_unexpected_error", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail="Agent encountered an unexpected error")

    # Auto-title session from first user message
    if len(db_messages) == 1:
        title = body.content[:60] + ("..." if len(body.content) > 60 else "")
        await crud.update_session_title(db, session_id, title)

    # Persist assistant message
    assistant_msg = await crud.add_message(
        db,
        session_id,
        "assistant",
        result["content"],
        sources=result["sources"],
        artifact=result["artifact"],
    )

    return ChatResponse(
        message=MessageResponse(
            id=assistant_msg.id,
            session_id=assistant_msg.session_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            sources=[SourceRef(**s) for s in (assistant_msg.sources or [])],
            artifact=ArtifactResponse(**assistant_msg.artifact) if assistant_msg.artifact else None,
            created_at=assistant_msg.created_at,
        ),
        intent=result["intent"],
    )

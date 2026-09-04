from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.models import Session, Message
from app.logging_config import get_logger
import uuid
from datetime import datetime

logger = get_logger(__name__)


async def create_session(db: AsyncSession, title: str = "New Chat", user_metadata: dict = None, llm_provider: str = "ollama") -> Session:
    session = Session(
        id=str(uuid.uuid4()),
        title=title,
        user_metadata=user_metadata or {},
        llm_provider=llm_provider,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info("session_created", session_id=session.id)
    return session


async def get_session(db: AsyncSession, session_id: str) -> Session | None:
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()


async def list_sessions(db: AsyncSession, limit: int = 50) -> list[Session]:
    result = await db.execute(select(Session).order_by(Session.updated_at.desc()).limit(limit))
    return list(result.scalars().all())


async def update_session_title(db: AsyncSession, session_id: str, title: str) -> Session | None:
    session = await get_session(db, session_id)
    if session:
        session.title = title
        session.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    result = await db.execute(delete(Session).where(Session.id == session_id))
    await db.commit()
    return result.rowcount > 0


async def add_message(db: AsyncSession, session_id: str, role: str, content: str, sources: list = None, artifact: dict = None) -> Message:
    msg = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role=role,
        content=content,
        sources=sources or [],
        artifact=artifact,
    )
    db.add(msg)
    # bump session updated_at
    session = await get_session(db, session_id)
    if session:
        session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages(db: AsyncSession, session_id: str) -> list[Message]:
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    return list(result.scalars().all())

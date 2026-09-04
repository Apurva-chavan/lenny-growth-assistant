from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db import crud
from app.api.schemas import SessionCreate, SessionResponse
from app.config import get_settings

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    session = await crud.create_session(
        db,
        title=body.title,
        user_metadata=body.user_metadata,
        llm_provider=settings.llm_provider,
    )
    return session


@router.get("", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    return await crud.list_sessions(db)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

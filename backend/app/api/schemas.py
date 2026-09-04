from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Sessions ---

class SessionCreate(BaseModel):
    title: str = "New Chat"
    user_metadata: dict = Field(default_factory=dict)


class SessionResponse(BaseModel):
    id: str
    title: str
    llm_provider: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Messages ---

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class SourceRef(BaseModel):
    source: str
    url: str
    excerpt: str


class ArtifactResponse(BaseModel):
    type: str  # html | markdown
    content: str


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: list[SourceRef] = []
    artifact: Optional[ArtifactResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    message: MessageResponse
    intent: str


# --- Health ---

class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    ollama_available: Optional[bool] = None
    index_chunks: int
    index_ready: bool
    db_connected: bool

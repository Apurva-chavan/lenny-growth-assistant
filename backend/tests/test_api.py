import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# --- Health ---

@pytest.mark.asyncio
async def test_health_endpoint(client):
    with patch("app.api.health.get_engine") as mock_engine, \
         patch("app.api.health.get_index_stats", return_value={"chunks": 10, "index_ready": True}), \
         patch("app.api.health.check_ollama_health", new_callable=AsyncMock, return_value=True):
        mock_conn = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)
        mock_conn.execute = AsyncMock()
        mock_engine.return_value.connect.return_value = mock_conn

        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "llm_provider" in data


# --- Sessions ---

@pytest.mark.asyncio
async def test_create_session(client):
    mock_session = MagicMock()
    mock_session.id = "test-session-id"
    mock_session.title = "New Chat"
    mock_session.llm_provider = "ollama"
    from datetime import datetime
    mock_session.created_at = datetime.utcnow()
    mock_session.updated_at = datetime.utcnow()

    with patch("app.api.sessions.crud.create_session", new_callable=AsyncMock, return_value=mock_session):
        resp = await client.post("/api/v1/sessions", json={"title": "New Chat"})
        assert resp.status_code == 201
        assert resp.json()["id"] == "test-session-id"


@pytest.mark.asyncio
async def test_get_session_not_found(client):
    with patch("app.api.sessions.crud.get_session", new_callable=AsyncMock, return_value=None):
        resp = await client.get("/api/v1/sessions/nonexistent")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_sessions(client):
    with patch("app.api.sessions.crud.list_sessions", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/api/v1/sessions")
        assert resp.status_code == 200
        assert resp.json() == []


# --- Messages ---

@pytest.mark.asyncio
async def test_send_message_session_not_found(client):
    with patch("app.api.messages.crud.get_session", new_callable=AsyncMock, return_value=None):
        resp = await client.post("/api/v1/sessions/bad-id/messages", json={"content": "hello"})
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_send_message_success(client):
    from datetime import datetime
    mock_session = MagicMock()
    mock_session.id = "sess-1"

    mock_user_msg = MagicMock()
    mock_user_msg.role = "user"
    mock_user_msg.content = "What is product-market fit?"

    mock_assistant_msg = MagicMock()
    mock_assistant_msg.id = "msg-2"
    mock_assistant_msg.session_id = "sess-1"
    mock_assistant_msg.role = "assistant"
    mock_assistant_msg.content = "Product-market fit means..."
    mock_assistant_msg.sources = []
    mock_assistant_msg.artifact = None
    mock_assistant_msg.created_at = datetime.utcnow()

    with patch("app.api.messages.crud.get_session", new_callable=AsyncMock, return_value=mock_session), \
         patch("app.api.messages.crud.add_message", new_callable=AsyncMock, return_value=mock_assistant_msg), \
         patch("app.api.messages.crud.get_messages", new_callable=AsyncMock, return_value=[mock_user_msg]), \
         patch("app.api.messages.crud.update_session_title", new_callable=AsyncMock), \
         patch("app.api.messages.run_agent", new_callable=AsyncMock, return_value={
             "content": "Product-market fit means...",
             "sources": [],
             "artifact": None,
             "intent": "rag",
         }):
        resp = await client.post("/api/v1/sessions/sess-1/messages", json={"content": "What is product-market fit?"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["message"]["role"] == "assistant"
        assert data["intent"] == "rag"


# --- Retriever ---

def test_chunk_text():
    from app.knowledge.retriever import _chunk_text
    text = " ".join([f"word{i}" for i in range(200)])
    chunks = _chunk_text(text, "test-source", "http://example.com", 50, 10)
    assert len(chunks) > 1
    assert all(c.source == "test-source" for c in chunks)
    assert all(len(c.text.split()) <= 50 for c in chunks)


# --- Agent routing ---

def test_intent_detection():
    from app.agent.agent import _detect_intent
    assert _detect_intent("write an essay about retention") == "ship30"
    assert _detect_intent("create artifact html dashboard") == "artifact_html"
    assert _detect_intent("what is product market fit?") == "rag"
    assert _detect_intent("generate markdown report") == "artifact_markdown"


# --- Ship30 skill ---

def test_ship30_prompt_structure():
    from app.skills.ship30 import build_ship30_prompt, SHIP30_SYSTEM
    from app.knowledge.retriever import Chunk
    chunks = [Chunk(id="c1", source="ep-1", episode_url="http://x.com", text="Some insight about growth.", start_char=0, token_estimate=5)]
    system, user = build_ship30_prompt("How do you find PMF?", chunks)
    assert "Ship 30" in system
    assert "1,250" in system
    assert "How do you find PMF?" in user
    assert "ep-1" in user


# --- Artifact skill ---

def test_artifact_type_detection():
    from app.skills.artifact import detect_artifact_type
    assert detect_artifact_type("<!DOCTYPE html><html>...</html>") == "html"
    assert detect_artifact_type("---\ntitle: Test\n---\n# H1\n## H2\n## H3\n## H4") == "markdown"
    assert detect_artifact_type("Just a plain answer.") is None

"""
LLM client abstraction. Supports Anthropic, OpenAI, and Ollama.
Switch provider via LLM_PROVIDER env var without changing application code.
"""
import httpx
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)


async def chat_completion(messages: list[dict], system: str = "", max_tokens: int = 2048) -> str:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    logger.info("llm_request", provider=provider, message_count=len(messages))

    if provider == "anthropic":
        return await _anthropic(messages, system, max_tokens, settings)
    elif provider == "openai":
        return await _openai(messages, system, max_tokens, settings)
    elif provider == "ollama":
        return await _ollama(messages, system, max_tokens, settings)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


async def _anthropic(messages, system, max_tokens, settings) -> str:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    return response.content[0].text


async def _openai(messages, system, max_tokens, settings) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    full_messages = ([{"role": "system", "content": system}] if system else []) + messages
    response = await client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=max_tokens,
        messages=full_messages,
    )
    return response.choices[0].message.content


async def _ollama(messages, system, max_tokens, settings) -> str:
    full_messages = ([{"role": "system", "content": system}] if system else []) + messages
    payload = {
        "model": settings.ollama_model,
        "messages": full_messages,
        "stream": False,
        "options": {"num_predict": max_tokens},
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{settings.ollama_base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
    except httpx.ConnectError:
        raise RuntimeError(f"Ollama not reachable at {settings.ollama_base_url}. Is it running?")
    except httpx.TimeoutException:
        raise RuntimeError("Ollama request timed out. Try a smaller model or increase timeout.")


async def check_ollama_health(base_url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False

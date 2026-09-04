"""
Core agent: routes user messages to the right skill, manages context,
and returns structured responses.
"""
from app.agent.llm_client import chat_completion
from app.knowledge.retriever import search
from app.skills.ship30 import build_ship30_prompt
from app.skills.artifact import build_artifact_prompt, detect_artifact_type
from app.logging_config import get_logger

logger = get_logger(__name__)

RAG_SYSTEM = """You are the Lenny Growth Assistant — an expert on product management, growth, and startups.
You answer questions STRICTLY based on the provided transcript excerpts from Lenny's Podcast.

Rules:
1. Ground every claim in the provided sources. Cite the source name inline: (Source: episode-name).
2. If the sources don't contain enough information, say: "The available transcripts don't cover this specifically, but based on [source], ..."
3. Never fabricate quotes or statistics.
4. Be concise and direct. Use bullet points for lists.
5. Preserve conversation context for follow-up questions."""


def _detect_intent(message: str) -> str:
    """Simple keyword-based intent routing."""
    msg = message.lower()
    if any(k in msg for k in ["write an essay", "ship 30", "essay about", "write a post", "atomic essay"]):
        return "ship30"
    if any(k in msg for k in ["create artifact", "generate html", "make a document", "create a doc", "generate markdown", "create a report", "build a template"]):
        return "artifact_html" if "html" in msg else "artifact_markdown"
    return "rag"


async def run_agent(
    user_message: str,
    history: list[dict],
    session_id: str,
) -> dict:
    """
    Returns:
        {
            "content": str,
            "sources": list[dict],
            "artifact": dict | None,   # {"type": "html"|"markdown", "content": str}
            "intent": str,
        }
    """
    intent = _detect_intent(user_message)
    logger.info("agent_routing", session_id=session_id, intent=intent)

    # Retrieve relevant chunks for all intents
    chunks = search(user_message, top_k=6)
    sources = [{"source": c.source, "url": c.episode_url, "excerpt": c.text[:200]} for c in chunks]

    if not chunks:
        logger.warning("empty_retrieval", session_id=session_id, query=user_message)

    artifact = None

    if intent == "ship30":
        conv_summary = _summarize_history(history)
        system, user_prompt = build_ship30_prompt(user_message, chunks, conv_summary)
        content = await chat_completion(
            messages=[{"role": "user", "content": user_prompt}],
            system=system,
            max_tokens=2500,
        )
        # Ship30 essays are markdown artifacts
        artifact = {"type": "markdown", "content": content}
        content = "I've written a Ship 30 for 30 essay based on Lenny's transcripts. You can view it in the artifact panel →"

    elif intent in ("artifact_html", "artifact_markdown"):
        art_type = "html" if intent == "artifact_html" else "markdown"
        system, user_prompt = build_artifact_prompt(user_message, art_type, chunks, history)
        art_content = await chat_completion(
            messages=[{"role": "user", "content": user_prompt}],
            system=system,
            max_tokens=3000,
        )
        artifact = {"type": art_type, "content": art_content}
        content = f"I've generated a {art_type.upper()} artifact based on the transcripts. View it in the panel →"

    else:
        # Standard RAG conversation
        context_text = _build_context(chunks)
        messages = _build_messages(history, user_message, context_text)
        content = await chat_completion(
            messages=messages,
            system=RAG_SYSTEM,
            max_tokens=1500,
        )
        # Check if the model spontaneously generated an artifact
        detected = detect_artifact_type(content)
        if detected:
            artifact = {"type": detected, "content": content}
            content = f"I've generated a {detected.upper()} artifact. View it in the panel →"

    return {"content": content, "sources": sources, "artifact": artifact, "intent": intent}


def _build_context(chunks) -> str:
    if not chunks:
        return "No relevant transcript excerpts found."
    parts = []
    for c in chunks:
        parts.append(f"[Source: {c.source}]\n{c.text}")
    return "\n\n---\n\n".join(parts)


def _build_messages(history: list[dict], user_message: str, context: str) -> list[dict]:
    messages = []
    # Include last 8 turns for context window management
    for msg in history[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({
        "role": "user",
        "content": f"Relevant transcript excerpts:\n\n{context}\n\nQuestion: {user_message}",
    })
    return messages


def _summarize_history(history: list[dict]) -> str:
    if not history:
        return ""
    recent = history[-4:]
    return "\n".join(f"{m['role'].upper()}: {m['content'][:200]}" for m in recent)

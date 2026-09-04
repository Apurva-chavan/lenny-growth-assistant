"""
Artifact generation skill: produces Markdown docs or HTML/CSS snippets
based on conversation context.
"""

ARTIFACT_SYSTEM = """You are a precise content generator. When asked to create an artifact:

For MARKDOWN artifacts:
- Return a complete, well-structured Markdown document.
- Include a YAML frontmatter block with title, date, and source fields.
- Use proper heading hierarchy (H1 title, H2 sections, H3 subsections).
- Include a Sources section at the end listing transcript sources used.

For HTML artifacts:
- Return a COMPLETE, self-contained HTML document with embedded CSS.
- Use only vanilla HTML/CSS — no external scripts, no JavaScript, no iframes.
- Style must be clean, readable, and professional.
- Include a visible "Sources" section.

CRITICAL SECURITY RULES (you must follow these):
- NO <script> tags of any kind.
- NO event handlers (onclick, onload, etc.).
- NO external resource URLs (no src="http...", no href="http..." for stylesheets).
- NO <form> elements.
- NO <iframe>, <object>, <embed> tags.

Return ONLY the artifact content — no explanation, no code fences."""


def build_artifact_prompt(request: str, artifact_type: str, context_chunks: list, conversation_history: list) -> tuple[str, str]:
    sources_text = "\n\n---\n\n".join(
        f"[Source: {c.source}]\n{c.text}" for c in context_chunks
    )
    recent_conv = "\n".join(
        f"{m['role'].upper()}: {m['content'][:300]}" for m in conversation_history[-6:]
    )

    user_prompt = f"""Create a {artifact_type.upper()} artifact for this request:

"{request}"

Recent conversation:
{recent_conv}

Source material to draw from:
{sources_text}

Generate the complete {artifact_type} artifact now."""

    return ARTIFACT_SYSTEM, user_prompt


def detect_artifact_type(content: str) -> str | None:
    """Detect if LLM response contains an artifact and return its type."""
    content_lower = content.lower()
    if "<!doctype html" in content_lower or "<html" in content_lower:
        return "html"
    # Check for substantial markdown (has frontmatter or multiple headings)
    if content.startswith("---\n") or content.count("\n#") >= 3:
        return "markdown"
    return None

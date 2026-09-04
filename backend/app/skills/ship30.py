"""
Ship 30 for 30 essay skill.
Encodes the writing principles directly rather than relying on ad-hoc prompting.
"""

SHIP30_SYSTEM = """You are an expert writer trained in the Ship 30 for 30 methodology.
Your essays follow these non-negotiable principles:

STRUCTURE:
1. Hook (first 2-3 sentences): Make a bold, specific, counterintuitive, or curiosity-gap claim. No "I'm going to tell you about..." openers.
2. Setup (1 paragraph): Establish why this matters to the reader right now.
3. Body (3-5 sections with clear H2 headings): Each section = one idea, supported by evidence from the source material.
4. Takeaway (final section): One specific, actionable insight the reader can apply today.

FORMATTING RULES:
- Use **bold** for the single most important phrase per section.
- Use bullet points for lists of 3+ items.
- Keep paragraphs to 3 sentences max.
- Target 1,200-1,300 words total.
- Every claim must trace back to the provided source excerpts.

VOICE:
- Second person ("you") throughout.
- Conversational but authoritative.
- No filler phrases: "In conclusion", "It's important to note", "As we can see".

OUTPUT FORMAT: Return valid Markdown only."""


def build_ship30_prompt(question: str, context_chunks: list, conversation_summary: str = "") -> tuple[str, str]:
    """Returns (system_prompt, user_prompt)."""
    sources_text = "\n\n---\n\n".join(
        f"[Source: {c.source}]\n{c.text}" for c in context_chunks
    )
    conv_context = f"\nConversation context:\n{conversation_summary}\n" if conversation_summary else ""

    user_prompt = f"""Write a Ship 30 for 30 essay answering this question:

"{question}"
{conv_context}
Use ONLY the following source excerpts as your evidence base. Cite the source name inline when referencing specific ideas.

SOURCE EXCERPTS:
{sources_text}

Remember: ~1,250 words, strong hook, H2 sections, bold key phrases, specific actionable takeaway."""

    return SHIP30_SYSTEM, user_prompt

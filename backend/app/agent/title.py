"""Title generation for conversations.

Calls Groq with a short, focused prompt separate from the main extraction flow.
Failure here must never break the main chat workflow.
"""

import re
import httpx
from app.errors import AppError

_TITLE_SYSTEM = (
    "You generate short, descriptive titles for laptop search conversations. "
    "Rules:\n"
    "- Output ONLY the title text. No quotes, no markdown, no explanation.\n"
    "- 3 to 7 words. Maximum 80 characters. Plain text only.\n"
    "- Summarise what the user wants without inventing facts.\n"
    "- Examples: College Laptop Under 80000, ML and Programming Laptop, "
    "Lightweight Laptop With Long Battery\n"
    "- If the input is only a greeting or uninformative, reply: New chat"
)

# Patterns that indicate the message is just a greeting with no useful content.
_GREETING_RE = re.compile(
    r"^\s*(hi|hello|hey|hiya|howdy|greetings|good\s+(?:morning|afternoon|evening)|what'?s\s+up|sup)\s*[!.,]?\s*$",
    re.IGNORECASE,
)

_MAX_TITLE = 80


def _truncate_fallback(text: str) -> str:
    """Word-boundary fallback: truncate at last space before limit."""
    text = text.strip()
    if len(text) <= _MAX_TITLE:
        return text
    truncated = text[:_MAX_TITLE]
    last_space = truncated.rfind(" ")
    return truncated[:last_space] if last_space > 10 else truncated[:_MAX_TITLE]


def _sanitize(raw: str) -> str | None:
    """Strip surrounding quotes and check validity."""
    text = raw.strip().strip("\"'`").strip()
    if not text or text.lower() in ("new chat", ""):
        return None
    if len(text) > _MAX_TITLE:
        text = _truncate_fallback(text)
    # Reject anything that looks like JSON, code, or multi-line output
    if "\n" in text or text.startswith(("{", "[", "<")):
        return None
    return text


def is_meaningful(text: str) -> bool:
    """Return True if the message is worth generating a title from."""
    t = text.strip()
    if not t:
        return False
    if _GREETING_RE.match(t):
        return False
    if len(t.split()) < 3:
        return False
    return True


def generate_title(settings, first_message: str) -> tuple[str, str]:
    """Call Groq and return (title, status).

    Status is 'generated' on success or 'fallback' if the model call fails
    or returns unusable output. Never raises; always returns a usable pair.
    """
    fallback = _truncate_fallback(first_message)
    key = settings.groq_api_key.get_secret_value() if settings else ""
    if not key or key in ("CHANGE_ME", "<SET_LOCALLY>"):
        return fallback, "fallback"

    try:
        with httpx.Client(timeout=6.0) as client:
            response = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": settings.groq_model,
                    "messages": [
                        {"role": "system", "content": _TITLE_SYSTEM},
                        {"role": "user", "content": first_message[:500]},
                    ],
                    "max_completion_tokens": 30,
                    "temperature": 0.2,
                },
            )
    except Exception:
        return fallback, "fallback"

    if response.status_code != 200:
        return fallback, "fallback"

    try:
        raw = response.json()["choices"][0]["message"]["content"]
        title = _sanitize(raw)
        if title:
            return title, "generated"
    except Exception:
        pass

    return fallback, "fallback"

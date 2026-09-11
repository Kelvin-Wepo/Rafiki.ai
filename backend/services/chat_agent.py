"""Text replies for the dashboard chat, using the live ElevenLabs agent prompt."""

import re
from typing import Any, Dict, List, Optional

from services.elevenlabs_service import elevenlabs_service
from services.gemini_service import gemini_service
from utils.logger import get_logger

logger = get_logger(__name__)

_STAGE_DIRECTION = re.compile(r"\[[^\]]+\]")


def strip_stage_direction(text: str) -> str:
    return _STAGE_DIRECTION.sub("", text or "").strip()


def _role_of(message: Dict[str, Any]) -> str:
    role = str(message.get("role") or message.get("sender") or "").lower()
    if role in ("assistant", "ai", "agent"):
        return "assistant"
    return "user"


async def generate_text_reply(
    user_message: str,
    history: Optional[List[Dict[str, Any]]] = None,
    language: str = "en",
) -> str:
    """Reply in the live Rafiki agent's voice using Gemini + the agent prompt."""
    live = await elevenlabs_service.get_live_agent_config()
    name = (live.get("name") if live.get("success") else None) or "Rafiki"
    agent_prompt = (live.get("prompt") if live.get("success") else None) or ""
    first_message = strip_stage_direction(
        (live.get("first_message") if live.get("success") else None) or ""
    )

    turns = []
    for item in (history or [])[-16:]:
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        speaker = name if _role_of(item) == "assistant" else "User"
        turns.append(f"{speaker}: {content}")
    history_block = "\n".join(turns) if turns else "(no earlier messages)"

    lang_hint = (
        "Reply in Kiswahili unless the user writes in English."
        if language == "sw"
        else "Reply in the user's language (English or Kiswahili)."
    )

    prompt = f"""You are {name}, a Kenyan civic assistant that helps people with government services
(NTSA, KRA, Immigration, NRB, DCI, BRS, county services, and related Huduma/eCitizen flows).
{lang_hint}
Stay in character. Be warm, clear, and concise.
Do not ask for an eCitizen username or password.
Do not invent fees, receipt numbers, or appointment slots that were not given.
If you are unsure, say so and explain the next official step.

Agent instructions from ElevenLabs:
{agent_prompt[:6000] or "Help Kenyans access government services in English or Kiswahili."}

Tone example (do not repeat this greeting on every turn):
{first_message or "Habari, I am Rafiki."}

Recent conversation:
{history_block}

User: {user_message}
{name}:"""

    try:
        if not gemini_service._initialized:
            gemini_service.initialize()
        reply = await gemini_service.generate_plain_text(prompt)
        reply = strip_stage_direction(reply)
        if reply:
            return reply
    except Exception as exc:
        logger.error(f"Text chat generation failed: {exc}")

    if language == "sw":
        return "Samahani, sijaweza kujibu sasa hivi. Tafadhali jaribu tena."
    return "Sorry, I could not reply just now. Please try again."

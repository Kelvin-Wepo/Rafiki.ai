"""
Consent, handoff, and citizen-entropy helpers for AgentSession records.

Assumption: there was no Decision Graph or Citizen Entropy Score implementation
in the repo. Entropy here is a 0–1 uncertainty score stored on the session
record (1.0 = unknown citizen, lower as verified attributes accumulate).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

HANDOFF_COPY = {
    "en": "Got it — pulling that up with {agency} now, no need to re-verify.",
    "sw": "Sawa — ninaangalia hilo na {agency} sasa, hakuna haja ya kuthibitisha tena.",
}

CONSENT_PROMPT = {
    "en": (
        "Before I look up {agency}-specific details, I need your consent to use "
        "the information you already verified this session. Reply YES to continue "
        "or NO to stay with general guidance."
    ),
    "sw": (
        "Kabla sijaangalia maelezo ya {agency}, nahitaji idhini yako kutumia "
        "taarifa ulizothibitisha katika kipindi hiki. Jibu NDIYO kuendelea "
        "au HAPANA kubaki na mwongozo wa jumla."
    ),
}


def handoff_message(agency: str, language: str = "en") -> str:
    template = HANDOFF_COPY.get(language, HANDOFF_COPY["en"])
    return template.format(agency=agency)


def consent_prompt(agency: str, language: str = "en") -> str:
    template = CONSENT_PROMPT.get(language, CONSENT_PROMPT["en"])
    return template.format(agency=agency)


def has_consent(record: Dict[str, Any], agency: Optional[str], purpose: str = "session_guidance") -> bool:
    if not agency:
        return True
    grants = record.get("consent_grants") or {}
    grant = grants.get(agency) or grants.get(agency.upper())
    if not grant:
        return False
    if grant.get("revoked_at"):
        return False
    if not grant.get("granted", True):
        return False
    expires = grant.get("expires_at")
    if expires:
        try:
            if datetime.fromisoformat(expires) < datetime.utcnow():
                return False
        except ValueError:
            return False
    allowed_purpose = grant.get("purpose") or "session_guidance"
    # session_guidance is the weaker grant; record_lookup requires an explicit one
    if purpose == "record_lookup" and allowed_purpose != "record_lookup":
        return False
    return True


def grant_consent(
    record: Dict[str, Any],
    agency: str,
    purpose: str = "session_guidance",
) -> Dict[str, Any]:
    grants = record.setdefault("consent_grants", {})
    grants[agency] = {
        "agency": agency,
        "purpose": purpose,
        "granted": True,
        "granted_at": datetime.utcnow().isoformat(),
        "revoked_at": None,
        "expires_at": None,
    }
    _recompute_entropy(record)
    return grants[agency]


def revoke_consent(record: Dict[str, Any], agency: str) -> None:
    grants = record.setdefault("consent_grants", {})
    existing = grants.get(agency) or {}
    existing["granted"] = False
    existing["revoked_at"] = datetime.utcnow().isoformat()
    grants[agency] = existing
    _recompute_entropy(record)


def store_verified_attribute(
    record: Dict[str, Any],
    name: str,
    value_hash: str,
    source_agency: Optional[str] = None,
    confidence: float = 1.0,
) -> None:
    attrs = record.setdefault("verified_attributes", {})
    attrs[name] = {
        "name": name,
        "value_hash": value_hash,
        "source_agency": source_agency,
        "confidence": confidence,
        "verified_at": datetime.utcnow().isoformat(),
    }
    _recompute_entropy(record)


def record_handoff(
    record: Dict[str, Any],
    from_agency: Optional[str],
    to_agency: str,
    language: str = "en",
) -> Dict[str, Any]:
    message = handoff_message(to_agency, language)
    event = {
        "from_agency": from_agency,
        "to_agency": to_agency,
        "trigger": "user_message",
        "user_notified": True,
        "message_preview": message,
        "created_at": datetime.utcnow().isoformat(),
    }
    record.setdefault("handoffs", []).append(event)
    record["current_agency"] = to_agency
    logger.info(
        "whatsapp_handoff session_id=%s from=%s to=%s",
        record.get("id"),
        from_agency,
        to_agency,
    )
    return event


def can_reference_agency_data(record: Dict[str, Any], agency: Optional[str]) -> bool:
    """
    Gate for agency-specific VerifiedAttribute use.

    Public menus and requirements do not need this. Anything that would
    interpolate a previously verified PIN, ID, or similar must pass.
    """
    if not agency:
        return True
    if not record.get("verified_attributes"):
        return True
    return has_consent(record, agency, "record_lookup") or has_consent(
        record, agency, "session_guidance"
    )


def _recompute_entropy(record: Dict[str, Any]) -> None:
    attrs = record.get("verified_attributes") or {}
    grants = record.get("consent_grants") or {}
    active_grants = sum(1 for g in grants.values() if g.get("granted") and not g.get("revoked_at"))
    entropy = 1.0
    entropy -= min(0.5, 0.15 * len(attrs))
    entropy -= min(0.3, 0.05 * active_grants)
    record["entropy_score"] = round(max(0.05, entropy), 3)

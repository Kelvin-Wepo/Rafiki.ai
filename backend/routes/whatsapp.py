"""
WhatsApp Business Cloud API webhooks.

GET  /whatsapp/webhook  — Meta subscription verification (hub.challenge)
POST /whatsapp/webhook  — inbound messages (text + voice-note detection)
POST /whatsapp/simulate — DEBUG-only fixture replay, no Meta signature
"""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, JSONResponse

from rafiki_settings import get_settings
from services.whatsapp_router import WhatsAppRouter
from services.whatsapp_service import verify_webhook_signature
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


def _require_signature(settings, raw_body: bytes, header: Optional[str]) -> None:
    if settings.DEBUG and not settings.WHATSAPP_REQUIRE_SIGNATURE:
        return
    if not settings.WHATSAPP_APP_SECRET:
        if settings.DEBUG:
            logger.warning("WhatsApp signature skipped — WHATSAPP_APP_SECRET unset (DEBUG)")
            return
        raise HTTPException(status_code=503, detail="WhatsApp webhook is not configured")
    if not verify_webhook_signature(raw_body, header, settings.WHATSAPP_APP_SECRET):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


@router.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
):
    """Meta Cloud API subscription handshake."""
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token and hub_challenge:
        if hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN and settings.WHATSAPP_VERIFY_TOKEN:
            return PlainTextResponse(content=hub_challenge)
        raise HTTPException(status_code=403, detail="Verification token mismatch")
    raise HTTPException(status_code=400, detail="Missing hub.mode / hub.challenge / hub.verify_token")


@router.post("/webhook")
async def inbound_webhook(request: Request, background: BackgroundTasks):
    """
    Acknowledge immediately so Meta does not retry. Work runs in a background
    task — waiting on RAG or a Cloud API send inside the request would delay
    the 200 and duplicate inbound deliveries.
    """
    settings = get_settings()
    raw = await request.body()
    header = request.headers.get("X-Hub-Signature-256") or request.headers.get("x-hub-signature-256")
    _require_signature(settings, raw, header)

    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if payload.get("object") and payload.get("object") != "whatsapp_business_account":
        return JSONResponse({"status": "ignored"})

    background.add_task(_process_payload, payload)
    return JSONResponse({"status": "accepted"}, status_code=200)


@router.post("/simulate")
async def simulate_inbound(request: Request):
    """
    Replay a Cloud API payload locally without Meta.
    Disabled unless DEBUG=true.
    """
    settings = get_settings()
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    payload = await request.json()
    result = await _process_payload(payload)
    return {"status": "ok", "result": result}


async def _process_payload(payload: dict):
    try:
        router_impl = WhatsAppRouter()
        return await router_impl.handle_payload(payload)
    except Exception as exc:
        logger.error("WhatsApp payload processing failed: %s", exc, exc_info=True)
        return {"error": str(exc)}

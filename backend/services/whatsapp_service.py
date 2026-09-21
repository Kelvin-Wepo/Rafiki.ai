"""
WhatsApp Business Cloud API client.

Outbound text and template sends, media download, webhook signature checks.
No secrets here — tokens come from pydantic-settings.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional

import httpx

from rafiki_settings import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)

WHATSAPP_TEXT_LIMIT = 4096
CUSTOMER_WINDOW_HOURS = 24


def verify_webhook_signature(payload: bytes, header: Optional[str], app_secret: str) -> bool:
    """
    Validate X-Hub-Signature-256 from Meta.

    Header format: sha256=<hex digest of HMAC-SHA256(app_secret, raw_body)>
    """
    if not app_secret or not header:
        return False
    try:
        algo, provided = header.split("=", 1)
    except ValueError:
        return False
    if algo.lower() != "sha256":
        return False
    expected = hmac.new(app_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided)


def split_whatsapp_text(body: str, limit: int = WHATSAPP_TEXT_LIMIT) -> List[str]:
    """Split a reply so each chunk fits the Cloud API text limit."""
    text = (body or "").strip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]
    chunks: List[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        cut = remaining.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    return [c for c in chunks if c]


def within_customer_window(last_inbound_at_iso: Optional[str], now: Optional[float] = None) -> bool:
    """True if we may send a freeform message (user wrote within 24h)."""
    if not last_inbound_at_iso:
        return False
    try:
        from datetime import datetime
        last = datetime.fromisoformat(last_inbound_at_iso)
        epoch = last.timestamp()
    except (ValueError, TypeError):
        return False
    current = now if now is not None else time.time()
    return (current - epoch) < CUSTOMER_WINDOW_HOURS * 3600


class WhatsAppCloudClient:
    """Thin async client for Graph API message + media endpoints."""

    def __init__(self, http: Optional[httpx.AsyncClient] = None):
        self.settings = get_settings()
        self._http = http

    @property
    def configured(self) -> bool:
        return bool(
            self.settings.WHATSAPP_ACCESS_TOKEN and self.settings.WHATSAPP_PHONE_NUMBER_ID
        )

    def _base(self) -> str:
        version = self.settings.WHATSAPP_GRAPH_API_VERSION or "v21.0"
        return f"https://graph.facebook.com/{version}"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    async def _client(self) -> httpx.AsyncClient:
        if self._http is not None:
            return self._http
        return httpx.AsyncClient(timeout=20.0)

    async def send_text(self, to: str, body: str) -> Dict[str, Any]:
        if not self.configured:
            logger.warning("WhatsApp send skipped — credentials not configured")
            return {"success": False, "error": "whatsapp_not_configured", "simulated": True}
        chunks = split_whatsapp_text(body)
        last: Dict[str, Any] = {"success": True, "message_ids": []}
        owns_client = self._http is None
        client = await self._client()
        try:
            for chunk in chunks:
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "text",
                    "text": {"preview_url": False, "body": chunk},
                }
                url = f"{self._base()}/{self.settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
                response = await client.post(url, headers=self._headers(), json=payload)
                data = _safe_json(response)
                if response.status_code >= 400:
                    logger.error(
                        "WhatsApp text send failed status=%s body=%s",
                        response.status_code,
                        str(data)[:300],
                    )
                    return {
                        "success": False,
                        "error": data.get("error", {}).get("message", response.text[:200]),
                        "status_code": response.status_code,
                    }
                msg_id = (data.get("messages") or [{}])[0].get("id")
                last["message_ids"].append(msg_id)
        finally:
            if owns_client:
                await client.aclose()
        last["success"] = True
        return last

    async def send_template(
        self,
        to: str,
        template_name: Optional[str] = None,
        language: Optional[str] = None,
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        name = template_name or self.settings.WHATSAPP_TEMPLATE_NAME
        lang = language or self.settings.WHATSAPP_TEMPLATE_LANGUAGE or "en"
        if not name:
            return {"success": False, "error": "no_template_configured"}
        if not self.configured:
            return {"success": False, "error": "whatsapp_not_configured", "simulated": True}
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": name,
                "language": {"code": lang},
            },
        }
        if components:
            payload["template"]["components"] = components
        owns_client = self._http is None
        client = await self._client()
        try:
            url = f"{self._base()}/{self.settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
            response = await client.post(url, headers=self._headers(), json=payload)
            data = _safe_json(response)
            if response.status_code >= 400:
                return {
                    "success": False,
                    "error": data.get("error", {}).get("message", response.text[:200]),
                    "status_code": response.status_code,
                }
            return {"success": True, "data": data}
        finally:
            if owns_client:
                await client.aclose()

    async def mark_read(self, message_id: str) -> None:
        if not self.configured or not message_id:
            return
        owns_client = self._http is None
        client = await self._client()
        try:
            url = f"{self._base()}/{self.settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
            await client.post(
                url,
                headers=self._headers(),
                json={
                    "messaging_product": "whatsapp",
                    "status": "read",
                    "message_id": message_id,
                },
            )
        except Exception as exc:
            logger.debug("WhatsApp mark-read failed: %s", exc)
        finally:
            if owns_client:
                await client.aclose()

    async def download_media(self, media_id: str) -> Dict[str, Any]:
        """
        Download media bytes via the Cloud API two-step flow.
        Not used on the text path. Voice notes call this later — the extra
        Graph round-trip is a latency cost against the 5s voice target.
        """
        if not self.configured:
            return {"success": False, "error": "whatsapp_not_configured"}
        owns_client = self._http is None
        client = await self._client()
        try:
            meta_resp = await client.get(
                f"{self._base()}/{media_id}",
                headers=self._headers(),
            )
            meta = _safe_json(meta_resp)
            media_url = meta.get("url")
            if not media_url:
                return {"success": False, "error": "media_url_missing", "meta": meta}
            bin_resp = await client.get(media_url, headers=self._headers())
            if bin_resp.status_code >= 400:
                return {"success": False, "error": "media_download_failed"}
            return {
                "success": True,
                "content": bin_resp.content,
                "mime_type": meta.get("mime_type") or bin_resp.headers.get("content-type"),
            }
        finally:
            if owns_client:
                await client.aclose()

    async def send_reply(
        self,
        to: str,
        body: str,
        last_inbound_at_iso: Optional[str],
    ) -> Dict[str, Any]:
        """Freeform if inside the 24h window; otherwise a pre-approved template."""
        if within_customer_window(last_inbound_at_iso):
            return await self.send_text(to, body)
        logger.info("WhatsApp 24h window closed for %s — using template", to[:6] + "****")
        result = await self.send_template(to)
        if not result.get("success"):
            logger.warning("Template send failed after window expiry: %s", result.get("error"))
        return result


def _safe_json(response: httpx.Response) -> Dict[str, Any]:
    try:
        data = response.json()
        return data if isinstance(data, dict) else {"raw": data}
    except Exception:
        return {}

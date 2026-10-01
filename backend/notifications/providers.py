"""
SMS/WhatsApp provider abstraction.

- StubProvider: logs and succeeds (default; used in dev/tests, no network).
- MSG91Provider: real HTTP to MSG91. The endpoint host is a FIXED allowlisted
  constant — never built from user input — and every request has a timeout, so
  this is not an SSRF vector. The API key is read from settings (env only).
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Fixed, allowlisted outbound host. Do not interpolate user input into the URL.
MSG91_HOST = "control.msg91.com"
MSG91_SMS_URL = f"https://{MSG91_HOST}/api/v5/flow/"
_REQUEST_TIMEOUT = 10  # seconds


class ProviderError(Exception):
    pass


class BaseProvider:
    def send(self, to_phone: str, body: str, channel: str) -> str:
        """Return a provider message id on success, or raise ProviderError."""
        raise NotImplementedError


class StubProvider(BaseProvider):
    def send(self, to_phone: str, body: str, channel: str) -> str:
        logger.info("[stub-%s] to=%s body=%r", channel, to_phone, body)
        return "stub-message-id"


class MSG91Provider(BaseProvider):
    def __init__(self):
        if not settings.MSG91_API_KEY:
            raise ProviderError("MSG91_API_KEY is not configured.")
        self.api_key = settings.MSG91_API_KEY
        self.sender = settings.MSG91_SENDER_ID

    def send(self, to_phone: str, body: str, channel: str) -> str:
        # Phone/body go in the JSON body (never the URL). Host is the fixed
        # allowlisted constant above.
        payload = {
            "sender": self.sender,
            "mobiles": to_phone.lstrip("+"),
            "message": body,
        }
        headers = {"authkey": self.api_key, "Content-Type": "application/json"}
        try:
            resp = requests.post(
                MSG91_SMS_URL, json=payload, headers=headers, timeout=_REQUEST_TIMEOUT
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderError(f"MSG91 request failed: {exc}") from exc
        data = resp.json() if resp.content else {}
        return str(data.get("request_id") or data.get("message") or "msg91-ok")


def get_provider() -> BaseProvider:
    name = (settings.NOTIFICATION_PROVIDER or "stub").lower()
    if name == "msg91":
        return MSG91Provider()
    return StubProvider()

"""
DRF exception handler that wraps every error in the ``{ok:false,...}`` envelope
so clients never have to branch on DRF's default shapes. No tracebacks or
internal detail leak in the response body.
"""
from rest_framework.views import exception_handler as drf_exception_handler


def envelope_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        # Unhandled (500) — let Django's handler deal with it; do not leak here.
        return None

    detail = response.data
    code = getattr(exc, "default_code", "error")

    if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
        message = str(detail["detail"])
        payload = {"ok": False, "error": message, "code": code}
    else:
        # Serializer / validation errors: keep the field map under `details`.
        message = "Validation failed."
        payload = {"ok": False, "error": message, "code": "validation_error", "details": detail}

    response.data = payload
    return response

"""
Standard response envelope: ``{ok, data}`` on success, ``{ok, error, code}`` on
failure. Mirrors the source app's ``{ok,data}|{ok,error,code}`` result shape so
the Vue client has one predictable contract everywhere.
"""
from rest_framework.response import Response


def ok(data=None, status=200):
    return Response({"ok": True, "data": data}, status=status)


def err(message, code="error", status=400, details=None):
    body = {"ok": False, "error": message, "code": code}
    if details is not None:
        body["details"] = details
    return Response(body, status=status)

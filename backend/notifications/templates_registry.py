"""
Server-controlled, versioned message templates (DLT-safe: fixed structure, only
approved variables filled). One builder per event.
"""
from common.money import format_paise_inr

TEMPLATE_VERSION = "v1"


def _rupees(paise):
    return format_paise_inr(abs(paise or 0))


def enrollment(ctx):
    return (
        f"Hi {ctx['member_name']}, welcome to {ctx['gym_name']}! Your {ctx['plan_name']} "
        f"membership is active till {ctx['end_date']}. Paid {_rupees(ctx['amount_paise'])} "
        f"(Invoice {ctx['invoice_number']})."
    )


def renewal(ctx):
    return (
        f"Hi {ctx['member_name']}, your {ctx['gym_name']} membership is renewed "
        f"({ctx['plan_name']}) till {ctx['end_date']}. Paid {_rupees(ctx['amount_paise'])} "
        f"(Invoice {ctx['invoice_number']})."
    )


def refund(ctx):
    return (
        f"Hi {ctx['member_name']}, a refund of {_rupees(ctx['amount_paise'])} has been "
        f"processed by {ctx['gym_name']} (Invoice {ctx['invoice_number']})."
    )


def correction(ctx):
    return (
        f"Hi {ctx['member_name']}, your {ctx['gym_name']} membership was updated. "
        f"New validity: {ctx['end_date']}."
    )


def cancellation(ctx):
    return (
        f"Hi {ctx['member_name']}, your {ctx['gym_name']} membership has been cancelled "
        f"effective {ctx['effective_date']}."
    )


def test(ctx):
    return f"Test message from {ctx['gym_name']} — your notifications are working."


BUILDERS = {
    "enrollment": enrollment,
    "renewal": renewal,
    "refund": refund,
    "correction": correction,
    "cancellation": cancellation,
    "test": test,
}


def render(event: str, ctx: dict) -> str:
    builder = BUILDERS.get(event)
    if not builder:
        raise ValueError(f"No template for event {event!r}")
    return builder(ctx)

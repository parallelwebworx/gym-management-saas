"""
Phone normalization to E.164 for India (+91), mirroring the source app's
convention. Accepts common local formats and returns a canonical ``+91XXXXXXXXXX``
string, or raises ``ValueError`` for anything that isn't a valid 10-digit Indian
mobile number.
"""
import re

_DIGITS = re.compile(r"\D+")


def normalize_phone_in(raw: str) -> str:
    """Normalize an Indian phone number to E.164 (+91XXXXXXXXXX).

    Handles: leading +91 / 91 / 0, spaces, dashes, parentheses. Indian mobile
    numbers are 10 digits starting 6-9.
    """
    if raw is None:
        raise ValueError("Phone is required.")
    digits = _DIGITS.sub("", str(raw).strip())

    # Strip country / trunk prefixes down to the 10-digit subscriber number.
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]

    if len(digits) != 10 or digits[0] not in "6789":
        raise ValueError(
            "Enter a valid 10-digit Indian mobile number (optionally +91 prefixed)."
        )
    return f"+91{digits}"

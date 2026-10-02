"""Money helpers. All amounts are integer paise."""

_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
         "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
         "Seventeen", "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def format_paise_inr(paise: int) -> str:
    """Format paise as e.g. '₹1,500.00' using Indian digit grouping."""
    rupees = paise // 100
    pennies = paise % 100
    s = str(rupees)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        import re
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        grouped = f"{head},{tail}"
    else:
        grouped = s
    return f"₹{grouped}.{pennies:02d}"


def _two_digits(n: int) -> str:
    if n < 20:
        return _ONES[n]
    return (_TENS[n // 10] + (" " + _ONES[n % 10] if n % 10 else "")).strip()


def _three_digits(n: int) -> str:
    out = ""
    if n >= 100:
        out += _ONES[n // 100] + " Hundred"
        n %= 100
        if n:
            out += " "
    if n:
        out += _two_digits(n)
    return out


def rupees_in_words(paise: int) -> str:
    """Indian-system amount in words, e.g. 'One Thousand Five Hundred Rupees Only'."""
    rupees = abs(paise) // 100
    pennies = abs(paise) % 100
    if rupees == 0:
        words = "Zero"
    else:
        parts = []
        crore = rupees // 10_000_000
        rupees %= 10_000_000
        lakh = rupees // 100_000
        rupees %= 100_000
        thousand = rupees // 1000
        rest = rupees % 1000
        if crore:
            parts.append(_two_digits(crore) + " Crore")
        if lakh:
            parts.append(_two_digits(lakh) + " Lakh")
        if thousand:
            parts.append(_two_digits(thousand) + " Thousand")
        if rest:
            parts.append(_three_digits(rest))
        words = " ".join(parts)
    result = f"{words} Rupees"
    if pennies:
        result += f" and {_two_digits(pennies)} Paise"
    return result + " Only"

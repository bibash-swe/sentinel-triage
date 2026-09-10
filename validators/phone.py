"""Phone number normalisation for SMS delivery."""


def strip_formatting(number: str) -> str:
    """Removes spaces, dashes and parentheses."""
    for ch in " -()":
        number = number.replace(ch, "")
    return number


def to_e164(number: str, country_code: str) -> str:
    """Renders a number in E.164 form for the SMS gateway."""
    digits = strip_formatting(number)
    if digits.startswith("0"):
        digits = digits[1:]
    return f"+{country_code}{digits}"


def is_plausible(number: str) -> bool:
    """Length check before paying for a carrier lookup."""
    return 7 <= len(strip_formatting(number)) <= 15

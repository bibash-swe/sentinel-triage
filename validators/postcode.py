"""UK postcode handling for delivery routing."""

import re

_OUTWARD = re.compile(r"^[A-Z]{1,2}[0-9][A-Z0-9]?$")


def split(postcode: str) -> tuple[str, str]:
    """Splits into outward and inward parts."""
    cleaned = postcode.replace(" ", "").upper()
    return cleaned[:-3], cleaned[-3:]


def is_valid(postcode: str) -> bool:
    """Whether the postcode is well formed."""
    outward, inward = split(postcode)
    return _OUTWARD.match(outward) is not None and len(inward) == 3


def area_of(postcode: str) -> str:
    """The alphabetic area prefix used to pick a depot, e.g. SW1A 1AA -> SW."""
    outward, _inward = split(postcode)
    return outward[0:2]

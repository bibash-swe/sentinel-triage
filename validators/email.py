"""Email address handling for account identity."""

import re

_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$")


def normalise(address: str) -> str:
    """Canonical form used as the account lookup key."""
    return address.strip().lower()


def is_valid(address: str) -> bool:
    """Whether the address looks deliverable."""
    return _PATTERN.match(normalise(address)) is not None


def same_account(left: str, right: str) -> bool:
    """Whether two addresses identify the same account."""
    return normalise(left) == normalise(right)

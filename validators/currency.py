"""Money formatting for invoices."""

from decimal import Decimal

SYMBOLS = {"GBP": "£", "USD": "$", "EUR": "€"}


def to_minor_units(amount: Decimal) -> int:
    """Converts a decimal amount to integer minor units for the ledger."""
    return int(amount * 100)


def apply_discount(amount: Decimal, percent: Decimal) -> Decimal:
    """Reduces an amount by a percentage."""
    return amount - (amount * percent / 100)


def format_amount(amount: Decimal, code: str) -> str:
    """Renders an amount with its currency symbol."""
    return f"{SYMBOLS[code]}{amount:.2f}"

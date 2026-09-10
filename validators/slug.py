"""URL slug generation for public article pages."""

import re

_SEPARATORS = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    """Turns a title into a URL-safe slug."""
    return _SEPARATORS.sub("-", title.lower()).strip("-")


def truncate(slug: str, limit: int) -> str:
    """Shortens a slug without cutting a word in half."""
    if len(slug) <= limit:
        return slug
    return slug[:limit].rsplit("-", 1)[0]


def uniquify(slug: str, taken: set[str]) -> str:
    """Appends a counter until the slug is free."""
    candidate, n = slug, 1
    while candidate in taken:
        n += 1
        candidate = f"{slug}-{n}"
    return candidate

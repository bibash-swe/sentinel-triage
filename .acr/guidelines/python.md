# Python review guidelines

These apply to every Python file in this repository.

## Logging

Logging calls must use lazy `%`-style formatting, never f-strings. An f-string is
evaluated even when the record is filtered out, and it loses the structured
arguments our JSON formatter depends on.

```python
logger.error("EXTRACTION_FAILED: %s", exc)   # yes
logger.error(f"EXTRACTION_FAILED: {exc}")    # no
```

## Exceptions

Every custom exception in this codebase must derive from a shared package base
class (`SentinelError`), never directly from `Exception`, so callers can catch
the whole family at a boundary.

## Typing

Public functions and `__init__` parameters carry type annotations. An untyped
collaborator is invisible to mypy and to the dependency graph.

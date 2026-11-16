"""Error types for seal. Every error carries a stable process exit code."""
from __future__ import annotations

EXIT_OK = 0
EXIT_UNEXPECTED = 1
EXIT_ERROR = 2
EXIT_USAGE = 3


class SealError(Exception):
    """Base error. Subclasses override ``exit_code``."""

    exit_code = EXIT_ERROR

    def __init__(self, message: str, *, exit_code: int | None = None) -> None:
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class UsageError(SealError):
    exit_code = EXIT_USAGE


class ManifestError(SealError):
    exit_code = EXIT_ERROR


class PolicyError(SealError):
    exit_code = EXIT_ERROR


class TamperError(SealError):
    exit_code = EXIT_ERROR

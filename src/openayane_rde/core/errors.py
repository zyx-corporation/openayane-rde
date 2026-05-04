"""Explicit exceptions for OpenAyane RDE."""

from __future__ import annotations


class OpenAyaneError(Exception):
    """Base exception for all OpenAyane RDE errors."""


class ValidationError(OpenAyaneError):
    """Raised when a data model or schema validation fails."""


class DiffError(OpenAyaneError):
    """Raised when structural diff computation fails."""


class SemanticDeltaError(OpenAyaneError):
    """Raised when semantic delta estimation fails."""


class RDEEvaluationError(OpenAyaneError):
    """Raised when RDE evaluation fails."""


class PolicyDecisionError(OpenAyaneError):
    """Raised when policy bridge decision fails."""


class ExecutionError(OpenAyaneError):
    """Raised when runtime execution fails."""


class AuditError(OpenAyaneError):
    """Raised when audit log write or read fails."""

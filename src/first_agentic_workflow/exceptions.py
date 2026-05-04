"""Custom exception hierarchy for the application."""

from __future__ import annotations


class AppError(Exception):
    """Base exception for application errors."""


class ConfigError(AppError):
    """Raised when configuration is invalid or missing."""


class DataError(AppError):
    """Raised when data loading or processing fails."""


class BudgetExceededError(AppError):
    """Raised when a workflow exceeds its token budget."""

"""Backward-compatible logger module.

DEPRECATED: Use core.logging module for new code.
This module is kept for backward compatibility during migration.
"""
from core.logging import (
    StructuredLogger,
    get_logger,
    setup_logger,
    logger,
    with_correlation_id,
    log_event,
    TimingContext,
)

__all__ = [
    "StructuredLogger",
    "get_logger",
    "setup_logger",
    "logger",
    "with_correlation_id",
    "log_event",
    "TimingContext",
]

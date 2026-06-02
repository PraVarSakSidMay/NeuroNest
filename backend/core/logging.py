"""Structured logging system with correlation tracking and JSON output."""
import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Optional
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
request_context: ContextVar[dict] = ContextVar("request_context", default={})


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get() or "none",
            "context": {},
        }
        
        # Add extra context from log call
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add stack info
        if record.stack_info:
            log_data["stack"] = self.formatStack(record.stack_info)
        
        return json.dumps(log_data)


class StructuredLogger:
    """Structured logger with context support."""
    
    def __init__(self, name: str):
        self.name = name
        self._logger = logging.getLogger(name)
        
        # Ensure handler is added only once
        if not self._logger.handlers:
            # Use stderr so stdio-based integrations (MCP, CLI JSON streams)
            # can reserve stdout for machine-readable protocol messages.
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(StructuredFormatter())
            self._logger.addHandler(handler)
        
        self._logger.setLevel(logging.INFO)
    
    def _log(self, level: LogLevel, message: str, **context):
        record = self._logger.makeRecord(
            self.name,
            getattr(logging, level.value),
            "",
            0,
            message,
            (),
            None,
        )
        record.context = context
        self._logger.handle(record)
    
    def debug(self, message: str, **context):
        self._log(LogLevel.DEBUG, message, **context)
    
    def info(self, message: str, **context):
        self._log(LogLevel.INFO, message, **context)
    
    def warning(self, message: str, **context):
        self._log(LogLevel.WARNING, message, **context)
    
    def error(self, message: str, **context):
        self._log(LogLevel.ERROR, message, **context)
    
    def critical(self, message: str, **context):
        self._log(LogLevel.CRITICAL, message, **context)


def get_logger(name: str = "NeuroNest") -> StructuredLogger:
    return StructuredLogger(name)


def with_correlation_id(cid: Optional[str] = None) -> str:
    """Set correlation ID for current context."""
    cid = cid or str(uuid.uuid4())
    correlation_id.set(cid)
    return cid


class TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, logger: StructuredLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        duration_ms = (time.time() - self.start_time) * 1000
        self.logger.info(
            f"{self.operation} completed",
            operation=self.operation,
            duration_ms=round(duration_ms, 2),
        )


def log_event(logger: StructuredLogger, event: str, **data):
    """Log a structured event."""
    logger.info(event, event=event, **data)


# Convenience function for backward compatibility
def setup_logger(name: str = "NeuroNest"):
    return get_logger(name)


logger = get_logger()


# Pipeline stage logging helpers
def log_request_started(request_id: str, endpoint: str):
    log_event(logger, "request_started", request_id=request_id, endpoint=endpoint)


def log_request_completed(request_id: str, duration_ms: float):
    log_event(logger, "request_completed", request_id=request_id, duration_ms=duration_ms)


def log_provider_fallback(provider: str, reason: str):
    log_event(logger, "provider_fallback", provider=provider, reason=reason)


def log_emotion_detected(emotion: str, confidence: float):
    log_event(logger, "emotion_detected", emotion=emotion, confidence=confidence)


def log_transcription_completed(duration_ms: float, text_length: int):
    log_event(logger, "transcription_completed", duration_ms=duration_ms, text_length=text_length)


def log_tts_generated(voice_name: str):
    log_event(logger, "tts_generated", voice_name=voice_name)


def log_embedding_stored(interaction_id: str):
    log_event(logger, "embedding_stored", interaction_id=interaction_id)


def log_retrieval_completed(count: int):
    log_event(logger, "retrieval_completed", memory_count=count)


def log_pipeline_failed(error: str, stage: str):
    log_event(logger, "pipeline_failed", error=error, failed_stage=stage)

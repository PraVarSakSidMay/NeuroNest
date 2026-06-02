"""Domain exceptions with structured error handling."""
from enum import Enum
from typing import Optional, Any
import uuid


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    RATE_LIMITED = "RATE_LIMITED"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class DomainError(Exception):
    """Base domain exception with error code and context."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        super().__init__(self.message)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "message": self.message,
                "code": self.code.value,
                "details": self.details,
                "correlation_id": self.correlation_id,
            }
        }


class ValidationError(DomainError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ):
        details = {}
        if field is not None:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = str(value)
        super().__init__(message, ErrorCode.VALIDATION_ERROR, details)


class ProcessingError(DomainError):
    """Raised when processing step fails."""
    
    def __init__(
        self,
        message: str,
        step: Optional[str] = None,
        retryable: bool = False,
    ):
        details = {"retryable": retryable}
        if step is not None:
            details["failed_step"] = step
        super().__init__(message, ErrorCode.PROCESSING_ERROR, details)
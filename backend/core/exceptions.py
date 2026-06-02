"""Exception handlers for FastAPI application."""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from domain.exceptions import DomainError, ErrorCode


async def domain_error_handler(request: Request, exc: DomainError):
    """Handle domain errors with structured response."""
    return JSONResponse(
        status_code=400 if exc.code == ErrorCode.VALIDATION_ERROR else 500,
        content=exc.to_dict(),
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "code": "HTTP_ERROR",
                "details": {},
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions safely."""
    import logging
    logger = logging.getLogger("NeuroNest")
    logger.exception(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal Server Error",
                "code": "INTERNAL_ERROR",
                "details": {},
            }
        },
    )
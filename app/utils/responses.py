"""
API response utilities for standardized responses.

Provides utilities for creating consistent API responses across all endpoints.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from app.models.schemas import ErrorDetail, ErrorResponse


def generate_request_id() -> str:
    """Generate a unique request ID for tracking."""
    return f"req_{uuid.uuid4().hex[:12]}"


def create_error_response(
    status_code: int,
    error_type: str,
    message: str,
    details: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        status_code: HTTP status code
        error_type: Type of error (e.g., "ValidationError", "AuthenticationError")
        message: Human-readable error message
        details: Optional detailed error information
        request_id: Optional request identifier

    Returns:
        JSONResponse with standardized error format
    """
    error_response = ErrorResponse(
        success=False,
        error=error_type,
        message=message,
        details=details,
        request_id=request_id or generate_request_id(),
        timestamp=datetime.utcnow(),
    )

    return JSONResponse(status_code=status_code, content=error_response.model_dump())


def create_success_response(
    data: Any, message: str = "Operation completed successfully", status_code: int = 200
) -> JSONResponse:
    """
    Create a standardized success response.

    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code

    Returns:
        JSONResponse with standardized success format
    """
    if hasattr(data, "model_dump"):
        response_data = data.model_dump()
    elif isinstance(data, dict):
        response_data = data
    else:
        response_data = {"data": data}

    # Add standard success fields if not present
    if "success" not in response_data:
        response_data["success"] = True
    if "timestamp" not in response_data:
        response_data["timestamp"] = datetime.utcnow().isoformat()

    return JSONResponse(status_code=status_code, content=response_data)


def create_validation_error_response(
    validation_errors: List[Dict[str, Any]], request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create a standardized validation error response.

    Args:
        validation_errors: List of validation errors from Pydantic
        request_id: Optional request identifier

    Returns:
        JSONResponse with validation error details
    """
    details = []
    for error in validation_errors:
        details.append(
            ErrorDetail(
                code=error.get("type", "validation_error"),
                message=error.get("msg", "Validation failed"),
                field=".".join(str(loc) for loc in error.get("loc", [])),
            )
        )

    return create_error_response(
        status_code=422,
        error_type="ValidationError",
        message="Request validation failed",
        details=details,
        request_id=request_id,
    )


def add_request_id_to_request(request: Request) -> str:
    """
    Add a request ID to the request state and return it.

    Args:
        request: FastAPI request object

    Returns:
        Generated request ID
    """
    request_id = generate_request_id()
    request.state.request_id = request_id
    return request_id


def get_request_id(request: Request) -> Optional[str]:
    """
    Get the request ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Request ID if available, None otherwise
    """
    return getattr(request.state, "request_id", None)

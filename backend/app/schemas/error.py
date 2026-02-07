"""
Error response schemas for unified error contract.
All API errors must conform to this structure.
"""
from pydantic import BaseModel, Field
from typing import Optional


class ErrorResponse(BaseModel):
    """
    Unified error response model.
    
    All API errors (4xx, 5xx) must return this structure with:
    - error_code: Machine-readable error type
    - message: Human-readable error description
    - request_id: Request ID for tracing (from X-Request-ID)
    - details: Optional additional context (dict)
    """
    error_code: str = Field(
        ...,
        description="Machine-readable error code (e.g., 'VALIDATION_ERROR', 'NOT_FOUND')",
        examples=["VALIDATION_ERROR", "NOT_FOUND", "RATE_LIMIT_EXCEEDED"]
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Invalid request parameters", "Resource not found"]
    )
    request_id: str = Field(
        ...,
        description="Request ID for tracing (from X-Request-ID header)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    details: Optional[dict] = Field(
        default=None,
        description="Optional additional error context (field errors, validation details, etc.)",
        examples=[{"field": "email", "issue": "invalid format"}]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters",
                    "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    "details": {
                        "field": "email",
                        "issue": "invalid email format"
                    }
                },
                {
                    "error_code": "NOT_FOUND",
                    "message": "Resource not found",
                    "request_id": "660f9500-f39c-51e5-b827-557766550000",
                    "details": None
                }
            ]
        }
    }

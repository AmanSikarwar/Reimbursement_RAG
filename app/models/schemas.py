"""
Pydantic schemas for API request and response models.

This module defines all the data models used for API communication,
including request/response schemas and validation rules.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ReimbursementStatus(str, Enum):
    """Enumeration for reimbursement status values."""

    FULLY_REIMBURSED = "fully_reimbursed"
    PARTIALLY_REIMBURSED = "partially_reimbursed"
    DECLINED = "declined"


class QueryType(str, Enum):
    """Enumeration for query types in chatbot."""

    GENERAL = "general"
    EMPLOYEE_SPECIFIC = "employee_specific"
    STATUS_FILTER = "status_filter"
    DATE_RANGE = "date_range"
    AMOUNT_FILTER = "amount_filter"


# Invoice Analysis Models
class InvoiceAnalysisRequest(BaseModel):
    """Request model for invoice analysis."""

    employee_name: str = Field(..., description="Name of the employee")

    class Config:
        json_schema_extra = {"example": {"employee_name": "John Doe"}}


class LLMInvoiceAnalysisResponse(BaseModel):
    """
    Structured schema for LLM invoice analysis responses.
    
    This model defines the exact structure that the LLM must return
    to ensure consistent, parseable responses.
    """
    
    status: ReimbursementStatus = Field(
        ..., 
        description="Reimbursement status - must be one of: fully_reimbursed, partially_reimbursed, declined"
    )
    reason: str = Field(
        ..., 
        min_length=10,
        max_length=1000,
        description="Detailed explanation of the reimbursement decision"
    )
    total_amount: float = Field(
        ..., 
        ge=0.0,
        description="Total invoice amount extracted from the document - REQUIRED"
    )
    reimbursement_amount: float = Field(
        ..., 
        ge=0.0,
        description="Amount to be reimbursed based on policy analysis"
    )
    currency: str = Field(
        ..., 
        min_length=3,
        max_length=3,
        description="Currency code (INR, USD, EUR, etc.) - REQUIRED"
    )
    categories: List[str] = Field(
        ..., 
        description="Expense categories identified from the invoice - REQUIRED array"
    )
    policy_violations: Optional[List[str]] = Field(
        default=None, 
        description="List of policy violations, null if none found"
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        """Validate currency code format."""
        if not v.isupper() or len(v) != 3:
            raise ValueError("Currency must be a 3-letter uppercase code (e.g., INR, USD)")
        return v

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v):
        """Validate expense categories."""
        if not v or len(v) == 0:
            raise ValueError("At least one expense category must be provided")
        # Clean up categories
        return [cat.strip().lower() for cat in v if cat.strip()]

    @field_validator("reimbursement_amount")
    @classmethod
    def validate_reimbursement_amount(cls, v, info):
        """Validate that reimbursement amount doesn't exceed total amount."""
        if 'total_amount' in info.data and v > info.data['total_amount']:
            raise ValueError("Reimbursement amount cannot exceed total amount")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "status": "partially_reimbursed",
                "reason": "Hotel expenses approved but alcohol charges are not covered under company policy",
                "total_amount": 2500.0,
                "reimbursement_amount": 2000.0,
                "currency": "INR",
                "categories": ["accommodation", "meals"],
                "policy_violations": ["Alcohol expenses not reimbursable"]
            }
        }


class InvoiceAnalysisResult(BaseModel):
    """Model for individual invoice analysis result."""

    filename: str = Field(..., description="Name of the invoice file")
    status: ReimbursementStatus = Field(..., description="Reimbursement status")
    reason: str = Field(..., description="Detailed reason for the status")
    total_amount: Optional[float] = Field(None, description="Total invoice amount")
    reimbursement_amount: Optional[float] = Field(
        None, description="Amount to be reimbursed"
    )
    currency: Optional[str] = Field("USD", description="Currency of the amounts")
    categories: Optional[List[str]] = Field(
        None, description="Expense categories found"
    )
    policy_violations: Optional[List[str]] = Field(
        None, description="Policy violations if any"
    )


class ProcessingError(BaseModel):
    """Model for processing error information."""

    file: str = Field(..., description="Name of the file that caused the error")
    error: str = Field(..., description="Error message")


class InvoiceAnalysisResponse(BaseModel):
    """Response model for invoice analysis."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    employee_name: str = Field(..., description="Name of the employee")
    total_invoices: int = Field(..., description="Total number of invoices in the ZIP")
    processed_invoices: int = Field(
        ..., description="Number of successfully processed invoices"
    )
    failed_invoices: int = Field(..., description="Number of failed invoice processing")
    results: Optional[List[InvoiceAnalysisResult]] = Field(
        None, description="Analysis results"
    )
    processing_errors: Optional[List[ProcessingError]] = Field(
        None, description="Processing errors"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Processed 3 invoices successfully",
                "employee_name": "John Doe",
                "total_invoices": 3,
                "processed_invoices": 3,
                "failed_invoices": 0,
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


# Chatbot Models
class ChatMessage(BaseModel):
    """Model for individual chat message."""

    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Message timestamp",
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ["user", "assistant"]:
            raise ValueError('Role must be either "user" or "assistant"')
        return v


class SearchFilters(BaseModel):
    """Model for search filters in chatbot queries."""

    employee_name: Optional[str] = Field(None, description="Filter by employee name")
    status: Optional[ReimbursementStatus] = Field(
        None, description="Filter by reimbursement status"
    )
    date_from: Optional[datetime] = Field(
        None, description="Start date for date range filter"
    )
    date_to: Optional[datetime] = Field(
        None, description="End date for date range filter"
    )
    min_amount: Optional[float] = Field(None, description="Minimum amount filter")
    max_amount: Optional[float] = Field(None, description="Maximum amount filter")
    categories: Optional[List[str]] = Field(
        None, description="Filter by expense categories"
    )


class ChatRequest(BaseModel):
    """Request model for chatbot interaction."""

    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    session_id: Optional[str] = Field(
        None, description="Session identifier for conversation history"
    )
    filters: Optional[SearchFilters] = Field(
        None, description="Optional search filters"
    )
    include_sources: bool = Field(
        True, description="Whether to include source documents in response"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me all declined invoices for John Doe",
                "session_id": "user123",
                "include_sources": True,
            }
        }


class DocumentSource(BaseModel):
    """Model for document source information."""

    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Original filename")
    employee_name: str = Field(..., description="Employee name")
    status: ReimbursementStatus = Field(..., description="Reimbursement status")
    similarity_score: float = Field(..., description="Similarity score for the search")
    excerpt: Optional[str] = Field(
        None, description="Relevant excerpt from the document"
    )


class ChatResponse(BaseModel):
    """Response model for chatbot interaction."""

    response: str = Field(..., description="Bot response")
    session_id: str = Field(..., description="Session identifier")
    sources: Optional[List[DocumentSource]] = Field(
        None, description="Source documents used"
    )
    retrieved_documents: int = Field(0, description="Number of documents retrieved")
    query_type: QueryType = Field(
        QueryType.GENERAL, description="Type of query processed"
    )
    confidence_score: Optional[float] = Field(
        None, description="Confidence score of the response"
    )
    suggestions: Optional[List[str]] = Field(
        None, description="Suggested related queries for the user"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": "I found 2 declined invoices for John Doe...",
                "session_id": "user123",
                "retrieved_documents": 2,
                "query_type": "employee_specific",
                "suggestions": [
                    "Show me approved invoices for John Doe",
                    "What was the total amount of declined invoices?",
                    "Which invoices had policy violations?",
                ],
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


# Vector Store Models
class VectorDocument(BaseModel):
    """Model for documents stored in vector database."""

    id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document content")
    embedding: List[float] = Field(..., description="Vector embedding")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")

    class Config:
        arbitrary_types_allowed = True


class SearchQuery(BaseModel):
    """Model for vector search queries."""

    query_text: str = Field(..., description="Text to search for")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    score_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum similarity score"
    )


class SearchResult(BaseModel):
    """Model for vector search results."""

    document: VectorDocument = Field(..., description="Retrieved document")
    score: float = Field(..., description="Similarity score")

    class Config:
        arbitrary_types_allowed = True


# Streaming Models
class StreamingChunkType(str, Enum):
    """Enumeration for streaming chunk types."""

    METADATA = "metadata"
    CONTENT = "content"
    SUGGESTIONS = "suggestions"
    DONE = "done"
    ERROR = "error"


class StreamingChunk(BaseModel):
    """Model for streaming response chunks."""

    type: StreamingChunkType = Field(..., description="Type of the chunk")
    data: Optional[Any] = Field(None, description="Chunk data")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Chunk timestamp",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "content",
                "data": "This is a streaming response chunk...",
                "timestamp": "2024-06-20T10:30:00Z",
            }
        }


class StreamingMetadata(BaseModel):
    """Model for streaming metadata chunk."""

    sources: Optional[List[DocumentSource]] = Field(
        None, description="Source documents used"
    )
    retrieved_documents: int = Field(0, description="Number of documents retrieved")
    query_type: QueryType = Field(
        QueryType.GENERAL, description="Type of query processed"
    )
    filters_applied: Optional[Dict[str, Any]] = Field(
        None, description="Filters that were applied"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sources": [],
                "retrieved_documents": 2,
                "query_type": "employee_specific",
                "filters_applied": {"employee_name": "John Doe"},
            }
        }


class ChatStreamRequest(BaseModel):
    """Request model for streaming chatbot interaction."""

    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    session_id: Optional[str] = Field(
        None, description="Session identifier for conversation history"
    )
    filters: Optional[SearchFilters] = Field(
        None, description="Optional search filters"
    )
    include_sources: bool = Field(
        True, description="Whether to include source documents in response"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me all declined invoices for John Doe",
                "session_id": "user123",
                "include_sources": True,
            }
        }


# Invoice Analysis Streaming Models
class InvoiceAnalysisStreamingChunkType(str, Enum):
    """Enumeration for invoice analysis streaming chunk types."""

    METADATA = "metadata"
    POLICY_PROCESSING = "policy_processing"
    INVOICE_EXTRACTION = "invoice_extraction"
    INVOICE_ANALYSIS = "invoice_analysis"
    VECTOR_STORAGE = "vector_storage"
    RESULT = "result"
    PROGRESS = "progress"
    DONE = "done"
    ERROR = "error"


class InvoiceAnalysisStreamingChunk(BaseModel):
    """Model for invoice analysis streaming response chunks."""

    type: InvoiceAnalysisStreamingChunkType = Field(
        ..., description="Type of the chunk"
    )
    data: Optional[Any] = Field(None, description="Chunk data")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Chunk timestamp",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "invoice_analysis",
                "data": {"filename": "invoice1.pdf", "status": "processing"},
                "timestamp": "2024-06-20T10:30:00Z",
            }
        }


class InvoiceAnalysisStreamRequest(BaseModel):
    """Request model for streaming invoice analysis."""

    employee_name: str = Field(..., description="Name of the employee")

    class Config:
        json_schema_extra = {"example": {"employee_name": "John Doe"}}


class InvoiceAnalysisProgress(BaseModel):
    """Model for invoice analysis progress updates."""

    current_invoice: int = Field(..., description="Current invoice being processed")
    total_invoices: int = Field(..., description="Total number of invoices")
    processed_invoices: int = Field(..., description="Successfully processed invoices")
    failed_invoices: int = Field(..., description="Failed invoice processing count")
    current_filename: Optional[str] = Field(
        None, description="Current file being processed"
    )
    stage: str = Field(..., description="Current processing stage")

    class Config:
        json_schema_extra = {
            "example": {
                "current_invoice": 2,
                "total_invoices": 5,
                "processed_invoices": 1,
                "failed_invoices": 0,
                "current_filename": "invoice2.pdf",
                "stage": "analyzing",
            }
        }


# Enhanced Error Response Models
class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field name if validation error")


class ErrorResponse(BaseModel):
    """Standardized error response model."""

    success: bool = Field(False, description="Success status")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[List[ErrorDetail]] = Field(
        None, description="Detailed error information"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Error timestamp",
    )
    request_id: Optional[str] = Field(
        None, description="Request identifier for tracking"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "ValidationError",
                "message": "Request validation failed",
                "details": [
                    {
                        "code": "required",
                        "message": "Field is required",
                        "field": "employee_name",
                    }
                ],
                "timestamp": "2024-06-20T10:30:00Z",
                "request_id": "req_123456",
            }
        }


class SuccessResponse(BaseModel):
    """Standardized success response model."""

    success: bool = Field(True, description="Success status")
    message: str = Field(..., description="Success message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


# Health Check Models
class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ServiceHealth(BaseModel):
    """Health status for individual service."""

    name: str = Field(..., description="Service name")
    status: HealthStatus = Field(..., description="Service health status")
    message: Optional[str] = Field(None, description="Additional information")
    response_time_ms: Optional[float] = Field(
        None, description="Response time in milliseconds"
    )


class HealthResponse(BaseModel):
    """Comprehensive health check response."""

    status: HealthStatus = Field(..., description="Overall system health")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Health check timestamp",
    )
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    services: List[ServiceHealth] = Field(
        ..., description="Individual service health status"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-06-20T10:30:00Z",
                "uptime_seconds": 3600.5,
                "services": [
                    {
                        "name": "vector_store",
                        "status": "healthy",
                        "response_time_ms": 45.2,
                    },
                    {
                        "name": "llm_service",
                        "status": "healthy",
                        "response_time_ms": 123.4,
                    },
                ],
            }
        }

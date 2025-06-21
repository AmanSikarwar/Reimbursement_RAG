"""
Main FastAPI application module.

This module sets up the FastAPI application with all necessary configurations and route handlers.
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import desc

from app.api.routes import chatbot, health, invoice_analysis
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.services.vector_store import VectorStoreService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    This includes setting up logging, initializing the vector store,
    and preparing upload directories.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Track startup time for uptime calculations
    app.state.start_time = time.time()

    # Initialize vector store
    vector_store = VectorStoreService()
    await vector_store.initialize()
    app.state.vector_store = vector_store

    # Prepare upload directory
    upload_path = settings.get_upload_path()
    logger.info(f"Upload directory: {upload_path}")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")



app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Invoice Reimbursement System

A comprehensive AI-powered invoice reimbursement analysis system built with **FastAPI**, **LangChain**, and **Gemini LLM**. 
This system uses **RAG (Retrieval Augmented Generation)** to analyze invoice documents against HR policies and provides 
an intelligent chatbot interface for querying processed invoices.

### Key Features

- **Intelligent Invoice Analysis**: Analyze PDF invoices against HR reimbursement policies using Gemini LLM
- **Vector-Based Storage**: Store and retrieve invoice embeddings using Qdrant vector database
- **RAG Chatbot**: Interactive chatbot for querying processed invoices using natural language
- **Batch Processing**: Process multiple invoices at once via ZIP file upload
- **Duplicate Detection**: Prevent duplicate processing of the same invoices
- **Streaming Responses**: Real-time streaming for both analysis and chat responses
- **Comprehensive Analytics**: Track processing statistics and system health
- **Secure File Handling**: Secure upload and processing of sensitive documents

### Technical Stack

- **Backend**: FastAPI with async/await support
- **AI/ML**: Google Gemini LLM, LangChain, Sentence Transformers
- **Vector Database**: Qdrant for embeddings storage
- **Document Processing**: PyPDF2, custom PDF processors
- **Authentication**: Token-based (configurable)
- **Monitoring**: Comprehensive health checks and logging
""",
    summary="Enterprise-grade AI-powered invoice reimbursement analysis with RAG chatbot capabilities",
    contact={
        "name": "Developer",
        "email": "amansikarwaar@gmail.com",
        "url": "https://amansikarwar.github.io"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
        "identifier": "MIT"
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "**System Health Monitoring**\n\nComprehensive health check endpoints for monitoring system components including Qdrant vector database, Gemini LLM service, file system access, and overall application health. Essential for production monitoring and troubleshooting.",
        },
        {
            "name": "invoice-analysis",
            "description": "**Invoice Analysis Operations**\n\nAI-powered invoice processing endpoints that analyze PDF invoices against HR reimbursement policies using Google Gemini LLM. Supports batch processing, duplicate detection, and real-time streaming responses. Results are stored in vector database for future querying.",
        },
        {
            "name": "chatbot",
            "description": "**RAG-Based Chatbot**\n\nIntelligent conversational interface for querying processed invoice data using natural language. Powered by Retrieval Augmented Generation (RAG) with vector similarity search and LLM-generated responses. Supports conversation history, filtering, and source citations.",
        },
    ],
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
    ],
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    """
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
        },
    )


@app.get(
    "/",
    tags=["health"],
    summary="API Root & Information Hub",
    description="""
Welcome endpoint providing comprehensive API information, health status, and navigation links.
    
This endpoint serves as the main entry point for the Invoice Reimbursement System API,
offering an overview of available endpoints, system status, and documentation links.
""",
    response_description="Comprehensive API information with navigation and status",
    responses={
        200: {
            "description": "API information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Welcome to the Invoice Reimbursement System API",
                        "description": "AI-powered invoice reimbursement analysis with RAG chatbot",
                        "version": "1.0.0",
                        "status": "healthy",
                        "build_info": {
                            "environment": "development",
                            "debug_mode": True,
                            "supported_formats": ["PDF", "ZIP"],
                            "max_file_size_mb": 50
                        },
                        "documentation": {
                            "swagger_ui": "/docs",
                            "redoc": "/redoc",
                            "openapi_schema": "/openapi.json"
                        },
                        "endpoints": {
                            "health_comprehensive": "/api/v1/health",
                            "health_quick": "/health",
                            "invoice_analysis": "/api/v1/analyze-invoices",
                            "chatbot": "/api/v1/chat",
                            "chat_history": "/api/v1/chat/history/{session_id}"
                        },
                        "system_capabilities": [
                            "Batch invoice processing",
                            "AI-powered policy analysis",
                            "Vector-based document search",
                            "Conversational query interface",
                            "Real-time streaming responses"
                        ]
                    }
                }
            }
        }
    }
)
async def root():
    """
    Root endpoint providing comprehensive API information and status.
    
    Returns detailed information about the Invoice Reimbursement System API,
    including version, health status, available endpoints, and system capabilities.
    
    Returns:
        dict: Comprehensive API information including:
            - Welcome message and description
            - System version and health status
            - Build and environment information
            - Documentation links (Swagger, ReDoc, OpenAPI)
            - Available endpoints with descriptions
            - System capabilities and features
    """
    return {
        "message": "Welcome to the Invoice Reimbursement System API",
        "description": "AI-powered invoice reimbursement analysis with RAG chatbot",
        "version": settings.APP_VERSION,
        "status": "healthy",
        "build_info": {
            "environment": "development" if settings.DEBUG else "production",
            "debug_mode": settings.DEBUG,
            "supported_formats": settings.allowed_extensions_list,
            "max_file_size_mb": settings.MAX_FILE_SIZE,
            "llm_model": settings.LLM_MODEL,
            "vector_collection": settings.COLLECTION_NAME
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc", 
            "openapi_schema": "/openapi.json"
        },
        "endpoints": {
            "health_comprehensive": "/api/v1/health",
            "health_quick": "/health",
            "health_vector_store": "/api/v1/health/vector-store",
            "invoice_analysis": "/api/v1/analyze-invoices",
            "invoice_analysis_stream": "/api/v1/analyze-invoices/stream",
            "chatbot": "/api/v1/chat",
            "chatbot_stream": "/api/v1/chat/stream",
            "chat_history": "/api/v1/chat/history/{session_id}"
        },
        "system_capabilities": [
            "Batch invoice processing with ZIP file support",
            "AI-powered policy compliance analysis using Gemini LLM",
            "Vector-based document search with Qdrant",
            "Conversational query interface with RAG",
            "Real-time streaming responses",
            "Duplicate detection and prevention",
            "Comprehensive health monitoring",
            "Multi-format document support (PDF, ZIP)"
        ],
        "quick_start": {
            "step_1": "Check system health at /api/v1/health",
            "step_2": "Upload policy PDF and invoices ZIP to /api/v1/analyze-invoices",
            "step_3": "Query results using natural language at /api/v1/chat",
            "step_4": "Explore interactive docs at /docs"
        }
    }


@app.get(
    "/health",
    tags=["health"],
    summary="Quick Health Check",
    description="""
Lightning-fast health check endpoint optimized for automated monitoring.
    
This lightweight endpoint provides instant API availability confirmation without
testing individual components. Designed for high-frequency polling.
        
**Pro Tip**: For comprehensive system diagnostics, use `/api/v1/health` instead.
""",
    response_description="Instant health confirmation with minimal system information",
    responses={
        200: {
            "description": "Service is healthy and responding normally",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "timestamp": "2024-12-21T10:00:00.123456Z",
                        "uptime_seconds": 3600.75,
                        "response_time_ms": 2.1
                    }
                }
            }
        },
        503: {
            "description": "Service unavailable or starting up",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "version": "1.0.0",
                        "timestamp": "2024-12-21T10:00:00.123456Z",
                        "error": "Service starting up"
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Lightning-fast health check for load balancers and monitoring systems.
    
    Provides instant API availability confirmation with minimal resource usage.
    Perfect for high-frequency health checks and automated monitoring systems.
    
    This endpoint does NOT test individual components - use `/api/v1/health` 
    for comprehensive system diagnostics including vector database, LLM service,
    and file system health.
    
    Returns:
        dict: Quick health status with:
            - status: "healthy" if API is responding
            - version: Current application version
            - timestamp: High-precision response time
            - uptime_seconds: Time since application startup
    """
    import time
    start_request_time = time.perf_counter()
    
    response_data = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(time.time() - app.state.start_time, 2) if hasattr(app.state, 'start_time') else 0
    }
    
    # Add response time measurement
    response_data["response_time_ms"] = round((time.perf_counter() - start_request_time) * 1000, 2)
    
    return response_data


app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(invoice_analysis.router, prefix="/api/v1", tags=["invoice-analysis"])
app.include_router(chatbot.router, prefix="/api/v1", tags=["chatbot"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

"""
Main FastAPI application module.

This module sets up the FastAPI application with all necessary configurations,
middleware, and route handlers.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chatbot, health, invoice_analysis
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.middleware.security import (
    RateLimitMiddleware,
    RequestValidationMiddleware,
    SecurityHeadersMiddleware,
)
from app.services.vector_store import VectorStoreService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Invoice Reimbursement System")

    # Initialize vector store
    vector_store = VectorStoreService()
    await vector_store.initialize()
    app.state.vector_store = vector_store

    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Invoice Reimbursement System")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="An intelligent invoice reimbursement analysis system using LLMs and vector databases",
    lifespan=lifespan,
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_REQUESTS
)
app.add_middleware(RequestValidationMiddleware)

# Add CORS middleware
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


@app.get("/", tags=["health"])
async def root():
    """
    Root endpoint for health check.
    """
    return {
        "message": "Welcome to the Invoice Reimbursement System",
        "version": settings.APP_VERSION,
        "status": "healthy",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "version": settings.APP_VERSION}


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(invoice_analysis.router, prefix="/api/v1", tags=["invoice-analysis"])
app.include_router(chatbot.router, prefix="/api/v1", tags=["chatbot"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

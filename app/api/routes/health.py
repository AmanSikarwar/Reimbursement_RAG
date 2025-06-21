"""
Health check API routes.

Provides comprehensive health monitoring endpoints for monitoring.
"""

import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from app.core.config import settings
from app.models.schemas import HealthResponse, HealthStatus, ServiceHealth
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStoreService

router = APIRouter()
logger = logging.getLogger(__name__)

app_start_time = time.time()


def get_vector_store(request: Request) -> VectorStoreService:
    """Dependency to get vector store service from app state."""
    return request.app.state.vector_store


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Comprehensive Health Check",
    description="""
Comprehensive health check endpoint for monitoring system components.

This endpoint performs detailed health checks on all system components and 
dependencies, providing comprehensive status information for monitoring and 
troubleshooting purposes.

### Checked Components:
- **Vector Store (Qdrant)**: Database connectivity and responsiveness
- **LLM Service (Gemini)**: AI service availability and API access
- **File System**: Upload directory access and permissions
- **Application**: Overall application health and uptime

### Health Status Levels:
- **HEALTHY**: Component is fully operational
- **DEGRADED**: Component has issues but is partially functional
- **UNHEALTHY**: Component is not functioning properly

### Response Information:
- Individual service health status and response times
- Overall system health assessment
- Detailed error messages for troubleshooting
- System uptime and version information

### Response Time Metrics:
Each service includes response time measurements in milliseconds for 
performance monitoring and alerting.
""",
    response_description="Detailed health status of all system components",
    responses={
        200: {
            "description": "Health check completed (may include unhealthy services)",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-12-21T10:00:00Z",
                        "version": "1.0.0",
                        "uptime_seconds": 3600,
                        "services": [
                            {
                                "name": "vector_store",
                                "status": "healthy",
                                "message": "Qdrant connection successful",
                                "response_time_ms": 25.5
                            },
                            {
                                "name": "llm_service",
                                "status": "healthy",
                                "message": "Gemini API accessible",
                                "response_time_ms": 150.2
                            }
                        ]
                    }
                }
            }
        },
        500: {"description": "Critical system failure"}
    }
)
async def comprehensive_health_check(
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> HealthResponse:
    """
    Comprehensive health check endpoint.

    Checks the health of all system components including:
    - Vector database connectivity
    - LLM service availability
    - File system access

    Returns:
        HealthResponse with detailed system health information
    """
    services = []
    overall_status = HealthStatus.HEALTHY

    try:
        start_time = time.time()
        await vector_store.health_check()
        response_time = (time.time() - start_time) * 1000

        services.append(
            ServiceHealth(
                name="vector_store",
                status=HealthStatus.HEALTHY,
                message="Qdrant connection successful",
                response_time_ms=round(response_time, 2),
            )
        )
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        services.append(
            ServiceHealth(
                name="vector_store",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection failed: {str(e)}",
                response_time_ms=0,
            )
        )
        overall_status = HealthStatus.UNHEALTHY

    try:
        start_time = time.time()
        llm_service = LLMService()
        await llm_service.health_check()
        response_time = (time.time() - start_time) * 1000

        services.append(
            ServiceHealth(
                name="llm_service",
                status=HealthStatus.HEALTHY,
                message="Gemini API accessible",
                response_time_ms=round(response_time, 2),
            )
        )
    except Exception as e:
        logger.error(f"LLM service health check failed: {e}")
        services.append(
            ServiceHealth(
                name="llm_service",
                status=HealthStatus.UNHEALTHY,
                message=f"API error: {str(e)}",
                response_time_ms=0,
            )
        )
        overall_status = HealthStatus.UNHEALTHY

    try:
        import os

        start_time = time.time()

        upload_dir = settings.UPLOAD_DIRECTORY
        os.makedirs(upload_dir, exist_ok=True)

        test_file = os.path.join(upload_dir, ".health_check")
        with open(test_file, "w") as f:
            f.write("health_check")
        os.remove(test_file)

        response_time = (time.time() - start_time) * 1000

        services.append(
            ServiceHealth(
                name="file_system",
                status=HealthStatus.HEALTHY,
                message="File operations working",
                response_time_ms=round(response_time, 2),
            )
        )
    except Exception as e:
        logger.error(f"File system health check failed: {e}")
        services.append(
            ServiceHealth(
                name="file_system",
                status=HealthStatus.UNHEALTHY,
                message=f"File access error: {str(e)}",
                response_time_ms=0,
            )
        )
        overall_status = HealthStatus.UNHEALTHY

    uptime = time.time() - app_start_time

    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=round(uptime, 2),
        services=services,
    )


@router.get(
    "/health/quick",
    tags=["health"],
    summary="Quick Health Check",
    description="""
Lightweight health check endpoint optimized for load balancers and uptime monitoring.

This endpoint provides a fast, minimal health check without testing individual 
components.

### Use Cases:
- **Uptime Monitoring**: External monitoring services
- **Container Orchestration**: Docker health checks
- **High-Frequency Polling**: Systems requiring frequent status updates

### Performance:
- Minimal resource usage
- Sub-millisecond response time
- No external service dependencies
- Suitable for high-frequency requests

### Response Content:
- Simple status confirmation
- Uptime information
- Timestamp for monitoring
""",
    response_description="Simple OK status for load balancer health checks",
    responses={
        200: {
            "description": "Service is running and responding",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "timestamp": "2024-12-21T10:00:00Z",
                        "uptime": 3600.5
                    }
                }
            }
        }
    }
)
async def quick_health_check() -> dict:
    """
    Quick health check endpoint for load balancers.

    Returns:
        Simple OK response if service is running
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc),
        "uptime": round(time.time() - app_start_time, 2),
    }


@router.get("/health/vector-store", tags=["health"])
async def vector_store_health(
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> dict:
    """
    Vector store specific health check.

    Returns:
        Vector store health status and connection info
    """
    try:
        start_time = time.time()
        collection_info = await vector_store.get_collection_info()
        response_time = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "collection_info": collection_info,
            "timestamp": datetime.now(timezone.utc),
        }
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc),
        }

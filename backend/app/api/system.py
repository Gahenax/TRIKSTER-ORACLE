"""
System Routes: Health, Readiness, and Version endpoints
Production-grade system endpoints for monitoring and observability.
"""
import os
from fastapi import APIRouter, Request
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="", tags=["system"])


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: str


class ReadyResponse(BaseModel):
    """Readiness check response"""
    ready: bool
    checks: dict
    timestamp: str


class VersionResponse(BaseModel):
    """Version information response"""
    version: str
    build_commit: str
    api_name: str
    mode: str
    environment: str
    timestamp: str


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """
    Health check endpoint.
    Returns 200 if service is running, regardless of dependencies.
    """
    from app import __version__
    
    return HealthResponse(
        status="healthy",
        service="trickster-oracle-api",
        version=__version__,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.get("/ready", response_model=ReadyResponse)
async def readiness_check(request: Request):
    """
    Readiness check endpoint.
    Returns 200 if service is ready to accept requests.
    Can be extended with dependency checks (DB, cache, etc.)
    """
    checks = {
        "app_booted": True,
        # Add more checks here as needed:
        # "database": await check_database(),
        # "cache": await check_cache(),
    }
    
    ready = all(checks.values())
    
    return ReadyResponse(
        ready=ready,
        checks=checks,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.get("/version", response_model=VersionResponse)
async def get_version(request: Request):
    """
    Version endpoint with build information.
    Exposes git commit (if available) for deployment tracking.
    """
    from app import __version__
    
    build_commit = os.environ.get("BUILD_COMMIT", "unknown")
    environment = os.environ.get("ENV", "development")
    
    return VersionResponse(
        version=__version__,
        build_commit=build_commit,
        api_name="Trickster Oracle",
        mode="demo",
        environment=environment,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )

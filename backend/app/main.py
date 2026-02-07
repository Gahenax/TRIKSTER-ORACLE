"""
FastAPI Main Application
TRICKSTER-ORACLE Backend API

Maturation: A1 (Request ID + Logging) + A2 (System Routes)
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import __version__
from app.api import routes
from app.api import routes_v2  # B1: v2 API with token gating
from app.api import system
from app.middleware.request_id import RequestIDMiddleware
from app.logging import configure_logging, get_logger
from app.error_handlers import install_error_handlers
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.idempotency import IdempotencyMiddleware

# Configure structured logging
env = os.environ.get("ENV", "development")
use_json_logging = env in ["production", "staging"]
configure_logging(level=os.environ.get("LOG_LEVEL", "INFO"), use_json=use_json_logging)

logger = get_logger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    logger.info(
        "Trickster Oracle API starting",
        extra={"version": __version__, "environment": env}
    )
    yield
    logger.info("Trickster Oracle API shutting down")

# Create FastAPI app
app = FastAPI(
    title="Trickster Oracle API",
    description="Educational probabilistic analytics platform for sports events",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Install unified error contract handlers (P0: 404/405/422)
install_error_handlers(app)

# Rate limiting (P1: Phase 2)
from slowapi.errors import RateLimitExceeded
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add Request ID middleware (A1: Observability)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(IdempotencyMiddleware)  # P2: Idempotency

# CORS configuration (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production (E1)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(system.router)  # A2: System routes (health, ready, version)
app.include_router(routes.router)  # Existing v1 API routes
app.include_router(routes_v2.router)  # B1: v2 API routes with token gating


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Trickster Oracle API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready"
    }




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
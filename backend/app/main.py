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
from app.api import system
from app.middleware.request_id import RequestIDMiddleware
from app.logging import configure_logging, get_logger
from app.error_handlers import install_error_handlers
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler

# Configure structured logging
env = os.environ.get("ENV", "development")
use_json_logging = env in ["production", "staging"]
configure_logging(level=os.environ.get("LOG_LEVEL", "INFO"), use_json=use_json_logging)

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Trickster Oracle API",
    description="Educational probabilistic analytics platform for sports events",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Install unified error contract handlers (P0: 404/405/422)
install_error_handlers(app)

# Rate limiting (P1: Phase 2)
from slowapi.errors import RateLimitExceeded
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add Request ID middleware (A1: Observability)
app.add_middleware(RequestIDMiddleware)

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
app.include_router(routes.router)  # Existing API routes


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


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(
        "Trickster Oracle API starting",
        extra={"version": __version__, "environment": env}
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Trickster Oracle API shutting down")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
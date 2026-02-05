"""
FastAPI Main Application
TRICKSTER-ORACLE Backend API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import __version__
from app.api import routes

# Create FastAPI app
app = FastAPI(
    title="Trickster Oracle API",
    description="Educational probabilistic analytics platform for sports events",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "trickster-oracle-api",
        "version": __version__
    }


@app.get("/version")
async def get_version():
    """Get API version and configuration"""
    return {
        "version": __version__,
        "api_name": "Trickster Oracle",
        "mode": "demo",
        "max_simulations_demo": 1000,
        "disclaimer": "Educational analytics platform. Not for gambling predictions."
    }


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Trickster Oracle API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

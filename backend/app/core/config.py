"""
Configuration Management for TRICKSTER-ORACLE
Uses pydantic-settings for environment variable loading with validation
"""
import os
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables
    
    Required for Production:
    - DATABASE_URL: PostgreSQL connection string
    - REDIS_URL: Redis connection string
    
    Optional:
    - ENV: Environment identifier (local, staging, prod)
    - BUILD_COMMIT: Git commit SHA for observability
    - BUILD_TIME: Build timestamp
    - LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    
    # Environment & Build Info
    ENV: Literal["local", "staging", "prod"] = Field(
        default="local",
        description="Environment identifier"
    )
    BUILD_COMMIT: str = Field(
        default="unknown",
        description="Git commit SHA"
    )
    BUILD_TIME: str = Field(
        default="unknown",
        description="Build timestamp"
    )
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/trickster_local",
        description="PostgreSQL connection string"
    )
    
    # Redis Queue
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    REDIS_QUEUE_NAME: str = Field(
        default="queue:jobs",
        description="Redis queue key for jobs"
    )
    
    # Observability
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # CORS
    CORS_ORIGINS: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Worker
    WORKER_POLL_TIMEOUT_SECS: int = Field(
        default=5,
        description="Redis BRPOP timeout in seconds"
    )
    MAX_JOB_RETRIES: int = Field(
        default=2,
        description="Max retry attempts for failed jobs"
    )
    
    # Cleanup/Maintenance
    CLEANUP_JOBS_OLDER_THAN_DAYS: int = Field(
        default=30,
        description="Delete jobs older than N days during maintenance"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra env vars not in schema
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS as list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENV == "prod"
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging"""
        return self.ENV == "staging"


# Global settings instance
settings = Settings()

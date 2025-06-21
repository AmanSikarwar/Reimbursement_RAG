"""
Application configuration settings.

This module handles all configuration settings for the application,
including environment variables and default values with proper validation.
"""

import os
from enum import Enum
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """
    Application settings class with comprehensive validation.

    All settings are loaded from environment variables with fallback defaults.
    Includes validation for required settings and proper type conversion.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application settings
    APP_NAME: str = "Invoice Reimbursement System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: LogLevel = LogLevel.INFO

    # Security settings
    ALLOWED_HOSTS: str = Field(
        default="*", description="Comma-separated list of allowed hosts for CORS"
    )

    # API Keys
    GOOGLE_API_KEY: str = Field(
        default="", description="Google API key for Gemini LLM access"
    )

    # Qdrant Configuration
    QDRANT_URL: str = Field(
        default="http://localhost:6333", description="Qdrant vector database URL"
    )
    QDRANT_API_KEY: Optional[str] = Field(
        default=None, description="Qdrant API key for cloud instances"
    )

    # Vector Store Configuration
    COLLECTION_NAME: str = Field(
        default="invoice_reimbursements",
        min_length=1,
        description="Name of the Qdrant collection",
    )
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings",
    )
    VECTOR_SIZE: int = Field(default=384, gt=0, description="Size of embedding vectors")

    # File Upload Configuration
    MAX_FILE_SIZE: int = Field(default=50, gt=0, description="Maximum file size in MB")
    ALLOWED_EXTENSIONS: str = Field(
        default="pdf,zip", description="Comma-separated list of allowed file extensions"
    )
    UPLOAD_DIRECTORY: str = Field(
        default="uploads", description="Directory for file uploads"
    )

    # LLM Configuration
    LLM_MODEL: str = Field(default="gemini-2.5-flash", description="LLM model name")
    LLM_TEMPERATURE: float = Field(
        default=0.1, ge=0.0, le=2.0, description="LLM temperature (0.0-2.0)"
    )
    MAX_TOKENS: int = Field(
        default=4096, gt=0, description="Maximum tokens for LLM responses"
    )

    # Chat Configuration
    MAX_CONVERSATION_HISTORY: int = Field(
        default=20, gt=0, description="Maximum number of conversation history entries"
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> LogLevel:
        """Validate log level setting."""
        if isinstance(v, str):
            try:
                return LogLevel(v.upper())
            except ValueError:
                raise ValueError(
                    f"Invalid log level: {v}. Must be one of: {list(LogLevel)}"
                )
        return v

    @field_validator("ALLOWED_HOSTS")
    @classmethod
    def validate_allowed_hosts(cls, v: str) -> str:
        """Validate allowed hosts format."""
        if v == "*":
            return v

        # Check if it's a comma-separated list of valid hosts
        hosts = [host.strip() for host in v.split(",") if host.strip()]
        if not hosts:
            raise ValueError("ALLOWED_HOSTS cannot be empty when not '*'")

        return v

    @field_validator("QDRANT_URL")
    @classmethod
    def validate_qdrant_url(cls, v: str) -> str:
        """Validate Qdrant URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("QDRANT_URL must start with http:// or https://")
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Validate production-specific settings based on DEBUG flag."""
        if not self.DEBUG:
            errors = []

            if self.ALLOWED_HOSTS == "*":
                errors.append("ALLOWED_HOSTS should not be '*' in production")

            if errors:
                raise ValueError(
                    f"Production configuration errors: {'; '.join(errors)}"
                )

        return self

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed file extensions as a list."""
        return [
            ext.strip().lower()
            for ext in self.ALLOWED_EXTENSIONS.split(",")
            if ext.strip()
        ]

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.MAX_FILE_SIZE * 1024 * 1024

    @property
    def allowed_origins_list(self) -> List[str]:
        """Get allowed CORS origins as a list."""
        if self.ALLOWED_HOSTS == "*":
            return ["*"]
        return [
            origin.strip() for origin in self.ALLOWED_HOSTS.split(",") if origin.strip()
        ]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.DEBUG

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG

    def get_upload_path(self, filename: str = "") -> Path:
        """Get the full upload path for a file."""
        upload_dir = Path(self.UPLOAD_DIRECTORY)
        upload_dir.mkdir(parents=True, exist_ok=True)

        if filename:
            return upload_dir / filename
        return upload_dir

    def validate_required_settings(self) -> None:
        """
        Validate that all required settings are provided.

        Raises:
            ValueError: If required settings are missing.
        """
        errors = []

        if not self.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY environment variable is required")

        if errors:
            raise ValueError("Configuration errors: " + "; ".join(errors))

    def log_configuration(self) -> None:
        """Log current configuration (excluding sensitive data)."""
        import logging

        logger = logging.getLogger(__name__)

        config_info = {
            "app_name": self.APP_NAME,
            "version": self.APP_VERSION,
            "debug": self.DEBUG,
            "log_level": self.LOG_LEVEL.value,
            "qdrant_url": self.QDRANT_URL,
            "collection_name": self.COLLECTION_NAME,
            "embedding_model": self.EMBEDDING_MODEL,
            "llm_model": self.LLM_MODEL,
            "max_file_size_mb": self.MAX_FILE_SIZE,
            "allowed_extensions": self.allowed_extensions_list,
        }

        logger.info(f"Application configuration: {config_info}")


def create_settings() -> Settings:
    """
    Create and validate application settings.

    Returns:
        Settings: Validated settings instance

    Raises:
        SystemExit: If configuration validation fails
    """
    try:
        load_dotenv(override=True)

        settings = Settings()
        settings.validate_required_settings()
        return settings
    except Exception as e:
        print(f"Configuration error: {e}")
        print("Please check your environment variables and .env file")

        env_value = os.getenv("ENVIRONMENT", "NOT_SET")
        print(f"Debug: ENVIRONMENT environment variable value: '{env_value}'")

        raise SystemExit(1) from e


# Global settings instance
settings = create_settings()

if os.getenv("SKIP_CONFIG_LOG") != "true" and settings.DEBUG:
    settings.log_configuration()

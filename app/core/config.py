"""
Application configuration settings.

This module handles all configuration settings for the application,
including environment variables and default values.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings class.

    All settings are loaded from environment variables with fallback defaults.
    """

    # Application settings
    APP_NAME: str = "Invoice Reimbursement System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # Set to False for production
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"  # production, development, testing

    # Security settings
    SECRET_KEY: str = ""
    ALLOWED_HOSTS: str = "*"  # Comma-separated list of allowed origins
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # API Keys
    GOOGLE_API_KEY: str = ""

    # Qdrant Configuration
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None

    # Vector Store Configuration
    COLLECTION_NAME: str = "invoice_reimbursements"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_SIZE: int = 384

    # File Upload Configuration
    MAX_FILE_SIZE: int = 50  # MB
    ALLOWED_EXTENSIONS: str = "pdf,zip"
    UPLOAD_DIRECTORY: str = "uploads"

    # LLM Configuration
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 4096

    # Chat Configuration
    MAX_CONVERSATION_HISTORY: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Get allowed file extensions as a list."""
        return self.ALLOWED_EXTENSIONS.split(",")

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.MAX_FILE_SIZE * 1024 * 1024

    def validate_required_settings(self) -> None:
        """
        Validate that all required settings are provided.

        Raises:
            ValueError: If required settings are missing.
        """
        errors = []

        if not self.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY environment variable is required")

        if not self.SECRET_KEY:
            errors.append("SECRET_KEY environment variable is required")

        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                errors.append("DEBUG must be False in production")
            if self.ALLOWED_HOSTS == "*":
                errors.append("ALLOWED_HOSTS must be specified in production")

        if errors:
            raise ValueError("Configuration errors: " + "; ".join(errors))

    @property
    def allowed_origins_list(self) -> list[str]:
        """Get allowed CORS origins as a list."""
        if self.ALLOWED_HOSTS == "*":
            return ["*"]
        return [
            origin.strip() for origin in self.ALLOWED_HOSTS.split(",") if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"


# Global settings instance
settings = Settings()

# Validate settings on import
if os.getenv("SKIP_VALIDATION") != "true":
    try:
        settings.validate_required_settings()
    except ValueError as e:
        print(f"Configuration warning: {e}")
        print("Please set the required environment variables or create a .env file")

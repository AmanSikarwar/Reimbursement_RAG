"""
Configuration settings for the Streamlit frontend.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class StreamlitConfig:
    """Configuration class for Streamlit app settings."""

    # Backend API settings
    api_base_url: str = "http://localhost:8000"
    api_timeout: int = 300
    health_check_timeout: int = 5

    # UI settings
    default_currency: str = "INR"
    max_file_size_mb: int = 50
    supported_image_formats: Optional[list] = None
    results_per_page: int = 10

    # Cache settings
    cache_ttl_seconds: int = 300

    def __post_init__(self):
        """Post-initialization setup."""
        if self.supported_image_formats is None:
            self.supported_image_formats = ["pdf", "zip"]

        # Override with environment variables if present
        self.api_base_url = os.getenv("STREAMLIT_API_BASE_URL", self.api_base_url)
        self.api_timeout = int(os.getenv("STREAMLIT_API_TIMEOUT", self.api_timeout))
        self.default_currency = os.getenv(
            "STREAMLIT_DEFAULT_CURRENCY", self.default_currency
        )

    @property
    def analyze_invoices_url(self) -> str:
        """Get the invoice analysis endpoint URL."""
        return f"{self.api_base_url}/api/v1/analyze-invoices-stream"

    @property
    def chat_stream_url(self) -> str:
        """Get the chat stream endpoint URL."""
        return f"{self.api_base_url}/api/v1/chat/stream"

    @property
    def health_check_url(self) -> str:
        """Get the health check endpoint URL."""
        return f"{self.api_base_url}/api/v1/health/quick"

    @property
    def detailed_health_url(self) -> str:
        """Get the detailed health check endpoint URL."""
        return f"{self.api_base_url}/api/v1/health"


config = StreamlitConfig()

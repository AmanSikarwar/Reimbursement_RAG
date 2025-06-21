"""
Utility functions for the Streamlit frontend.

This module contains common utility functions used across multiple pages
of the Streamlit application.
"""

import time
from typing import Any, Dict

import httpx
import streamlit as st


def check_backend_health() -> Dict[str, Any]:
    """
    Check the health of the backend API.

    Returns:
        Dictionary containing health status and details
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get("http://localhost:8000/api/v1/health/quick")
            if response.status_code == 200:
                return {
                    "status": "online",
                    "data": response.json(),
                    "message": "Backend is online and responding",
                }
            else:
                return {
                    "status": "issues",
                    "data": None,
                    "message": f"Backend returned HTTP {response.status_code}",
                }
    except httpx.ConnectError:
        return {
            "status": "offline",
            "data": None,
            "message": "Backend is offline - Connection refused. Please start the FastAPI server.",
        }
    except httpx.TimeoutException:
        return {
            "status": "offline",
            "data": None,
            "message": "Backend is offline - Request timeout. Server may be overloaded.",
        }
    except Exception as e:
        return {
            "status": "offline",
            "data": None,
            "message": f"Backend health check failed: {str(e)}",
        }


def format_currency(amount: float, currency: str = "INR") -> str:
    """
    Format currency with proper symbol.

    Args:
        amount: The amount to format
        currency: Currency code (INR, USD, EUR)

    Returns:
        Formatted currency string
    """
    symbols = {"INR": "₹", "USD": "$", "EUR": "€"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def get_status_info(status: str) -> Dict[str, str]:
    """
    Get display information for reimbursement status.

    Args:
        status: Reimbursement status

    Returns:
        Dictionary with icon, color, and display text
    """
    status_lower = status.lower()

    if status_lower == "fully_reimbursed":
        return {"icon": "✅", "color": "success", "text": "Fully Reimbursed"}
    elif status_lower == "partially_reimbursed":
        return {"icon": "⚠️", "color": "warning", "text": "Partially Reimbursed"}
    elif status_lower == "declined":
        return {"icon": "❌", "color": "error", "text": "Declined"}
    else:
        return {"icon": "ℹ️", "color": "info", "text": status.replace("_", " ").title()}


def format_timestamp(timestamp: float) -> str:
    """
    Format a timestamp for display.

    Args:
        timestamp: Unix timestamp

    Returns:
        Formatted time string
    """
    return time.strftime("%H:%M:%S", time.localtime(timestamp))


def show_error_details(errors: list, title: str = "Errors"):
    """
    Display errors in a formatted expander.

    Args:
        errors: List of error messages or dictionaries
        title: Title for the error section
    """
    if not errors:
        return

    with st.expander(f"❌ {title} ({len(errors)})", expanded=False):
        for i, error in enumerate(errors, 1):
            if isinstance(error, dict):
                filename = error.get("file", "Unknown")
                error_msg = error.get("error", "Unknown error")
                st.error(f"{i}. {filename}: {error_msg}")
            else:
                st.error(f"{i}. {error}")


def create_download_data(results: list, format_type: str = "csv") -> str:
    """
    Create downloadable data from analysis results.

    Args:
        results: List of analysis results
        format_type: Format type (csv, json)

    Returns:
        Formatted data string
    """
    if format_type == "json":
        import json

        return json.dumps(results, indent=2, default=str)

    elif format_type == "csv":
        import csv
        import io

        output = io.StringIO()
        if results:
            fieldnames = results[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        return output.getvalue()

    return ""


def display_metrics_grid(metrics: Dict[str, Any], columns: int = 4):
    """
    Display metrics in a grid layout.

    Args:
        metrics: Dictionary of metric names and values
        columns: Number of columns in the grid
    """
    cols = st.columns(columns)

    for i, (label, value) in enumerate(metrics.items()):
        with cols[i % columns]:
            if isinstance(value, dict):
                st.metric(label, value.get("value", ""), value.get("delta", ""))
            else:
                st.metric(label, value)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_system_stats() -> Dict[str, Any]:
    """
    Get system statistics from the backend.

    Returns:
        Dictionary containing system statistics
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get("http://localhost:8000/api/v1/health")
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass

    return {}

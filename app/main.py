"""Create the FastAPI application.

Routes, the database and observability are added by later tasks.
"""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Build and return the application."""
    return FastAPI(
        title="Intelligent Inventory Dashboard API",
        version="0.1.0",
        description=(
            "Helps dealership managers see their vehicle stock, find vehicles that have "
            "been in stock for more than 90 days, and record what to do about them."
        ),
    )


app = create_app()

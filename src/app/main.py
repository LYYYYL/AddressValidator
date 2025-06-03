"""
Main entry point for the AddressValidator app.

This script initializes both the FastAPI backend and the NiceGUI frontend.
It exposes API endpoints for programmatic validation and a web UI for interactive use.
"""

from fastapi import FastAPI
from nicegui import ui

from address_validator.constants import VALIDATE_STATUS
from app.routers.validation_router import router as validation_router
from app.ui.home import build_home_page

app = FastAPI(title="AddressValidator Dummy API", version="0.1.0", description="FastAPI endpoints + NiceGUI frontend")


@app.get("/healthy")
def health_check():
    """
    Health check endpoint to verify that the API is running.

    Returns:
        dict: A simple JSON object with a "Healthy" status.
    """
    return {VALIDATE_STATUS: "Healthy"}


app.include_router(validation_router)

# Tell NiceGUI to build its page(s). This registers routes on the same `app`.
build_home_page()

# Run NiceGUI on top of FastAPI:
ui.run_with(app)

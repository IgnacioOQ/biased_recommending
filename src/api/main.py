"""
FastAPI application entry point.
"""

from fastapi import FastAPI

from src.api.routes import router


app = FastAPI(
    title="Recommender System Simulation API",
    description="REST API for managing recommender system simulations",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

"""
FastAPI application entry point.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router


app = FastAPI(
    title="Recommender System Simulation API",
    description="REST API for managing recommender system simulations",
    version="1.0.0",
)

# CORS configuration
# We always allow localhost:5173 for development
# We optionally allow a production URL via FRONTEND_URL env var
origins = ["http://localhost:5173"]

if frontend_url := os.getenv("FRONTEND_URL"):
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

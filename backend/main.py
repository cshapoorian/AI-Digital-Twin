"""
AI Digital Twin - FastAPI Backend Entry Point

This is the main entry point for the backend server.
Run with: uvicorn main:app --reload
"""

import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api import router
from db import init_db


# Simple in-memory rate limiter
class RateLimiter:
    """Rate limiter using sliding window algorithm."""

    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        """Check if request from client_ip is allowed."""
        now = time.time()
        minute_ago = now - 60

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > minute_ago
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False

        self.requests[client_ip].append(now)
        return True


rate_limiter = RateLimiter(requests_per_minute=30)

# Load environment variables from .env file
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes database on startup.
    """
    # Startup
    print("Initializing database...")
    init_db()
    print("Database initialized.")

    yield

    # Shutdown (cleanup if needed)
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AI Digital Twin API",
    description="Backend API for the AI Digital Twin chat application",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to API endpoints."""
    if request.url.path.startswith("/api/chat"):
        client_ip = request.client.host if request.client else "unknown"
        if not rate_limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down."
            )
    return await call_next(request)


# Include API routes
app.include_router(router, prefix="/api", tags=["chat"])


@app.get("/")
async def root():
    """Root endpoint - basic info."""
    return {
        "name": "AI Digital Twin API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

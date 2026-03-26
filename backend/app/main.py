"""
JARVIS FastAPI Application

Main entry point for the backend API.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.api import meetings, streaming, messages


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    from app.browser.browser_manager import browser_manager
    
    # Startup
    print(f"Starting {settings.app_name}...")
    await init_db()
    print("Database initialized")
    
    # Note: Browser is initialized lazily when first meeting join is requested
    # This avoids launching a browser if the API is only used for non-meeting tasks
    print("Browser automation ready (lazy initialization)")
    
    yield
    
    # Shutdown
    print(f"Shutting down {settings.app_name}...")
    
    # Shutdown browser if it was initialized
    if browser_manager.is_initialized:
        await browser_manager.shutdown()
        print("Browser shutdown complete")
    
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI Work Assistant - Attends meetings, manages messages, handles tasks",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(meetings.router, prefix="/api/v1/meetings", tags=["meetings"])
app.include_router(streaming.router, prefix="/api/v1/streaming", tags=["streaming"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["messages"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "jarvis-backend",
        "environment": settings.app_env,
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "name": settings.app_name,
        "description": "AI Work Assistant",
        "version": "1.0.0",
        "docs": "/docs",
    }

"""
Main FastAPI application
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from loguru import logger
import sys

from app.core.config import settings
from app.models.database import init_db
from app.api import auth, documents, summarization, analysis, export

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)
logger.add(
    settings.LOG_FILE,
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL
)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered document summarization and information extraction platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(summarization.router)
app.include_router(analysis.router)
app.include_router(export.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting application...")
    init_db()
    logger.info("Database initialized")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render main dashboard"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "app_name": settings.APP_NAME}
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/api/stats")
async def get_stats():
    """Get platform statistics"""
    from app.models.database import SessionLocal, User, Document, Summary

    db = SessionLocal()

    try:
        total_users = db.query(User).count()
        total_documents = db.query(Document).count()
        total_summaries = db.query(Summary).count()
        processed_documents = db.query(Document).filter(Document.processed == True).count()

        return {
            "total_users": total_users,
            "total_documents": total_documents,
            "total_summaries": total_summaries,
            "processed_documents": processed_documents
        }

    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

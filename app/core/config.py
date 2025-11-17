"""
Core configuration module
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "AI Document Summarization Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "change-this-in-production-use-strong-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "sqlite:///./document_platform.db"

    # File Upload
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    UPLOAD_DIR: str = "./uploads"
    PROCESSED_DIR: str = "./processed"

    # Model Settings
    DEFAULT_SUMMARIZATION_MODEL: str = "facebook/bart-large-cnn"
    DEFAULT_NER_MODEL: str = "en_core_web_sm"
    DEVICE: str = "cpu"

    # OCR Settings
    TESSERACT_CMD: str = "/usr/bin/tesseract"
    EASYOCR_LANGUAGES: List[str] = ["en"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(parents=True, exist_ok=True)


settings = Settings()

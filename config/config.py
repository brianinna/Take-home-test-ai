"""
Configuration settings for the invoice extraction service.
"""
import os
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Explicitly load .env file to ensure environment variables are correctly set
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Invoice Data Extraction API"
    
    # LLM settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    DEFAULT_LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.0  # Low temperature for deterministic outputs
    
    # PDF processing settings
    MAX_FILE_SIZE_MB: int = 10
    SUPPORTED_MIME_TYPES: list = ["application/pdf"]
    
    # OCR settings
    USE_TESSERACT: bool = True
    USE_VISION_API: bool = False  # Set to True to use GPT-4 Vision API
    
    # Extraction settings
    CONFIDENCE_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

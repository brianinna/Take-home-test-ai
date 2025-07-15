"""
Configuration settings for the invoice extraction service.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Explicitly load .env file to ensure environment variables are correctly set
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Invoice Data Extraction API"

    # --- Model Selection Strategy ---
    # Set to True to enable the multimodal pathway for scanned documents.
    # If False, all documents will be processed using the text model.
    USE_MULTIMODAL: bool = os.getenv("USE_MULTIMODAL", "true").lower() == "true"

    # --- Text Model Configuration ---
    TEXT_MODEL_API_KEY: Optional[str] = os.getenv("TEXT_MODEL_API_KEY")
    TEXT_MODEL_API_URL: Optional[str] = os.getenv("TEXT_MODEL_API_URL")
    TEXT_MODEL_NAME: str = os.getenv("TEXT_MODEL_NAME")

    # --- Multimodal Model Configuration ---
    MULTIMODAL_MODEL_API_KEY: Optional[str] = os.getenv("MULTIMODAL_MODEL_API_KEY")
    MULTIMODAL_MODEL_API_URL: Optional[str] = os.getenv("MULTIMODAL_MODEL_API_URL")
    MULTIMODAL_MODEL_NAME: str = os.getenv("MULTIMODAL_MODEL_NAME")

    # --- General Model Settings ---
    LLM_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.0"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))

    # --- PDF Processing Settings ---
    MAX_FILE_SIZE_MB: int = 10
    SUPPORTED_MIME_TYPES: list = ["application/pdf"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
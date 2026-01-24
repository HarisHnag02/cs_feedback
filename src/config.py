"""
Configuration module for the Freshdesk Feedback AI Analysis System.

This module loads and validates environment variables required for the application.
It provides a centralized configuration management system using pydantic for
type validation and environment variable handling.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        freshdesk_api_key: API key for Freshdesk authentication
        openai_api_key: API key for OpenAI services
        freshdesk_domain: Freshdesk domain URL (optional, defaults to None)
        log_level: Logging level for the application (default: INFO)
    """
    
    # Required API Keys
    freshdesk_api_key: str = Field(
        ...,
        description="Freshdesk API key for authentication"
    )
    
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key for AI analysis"
    )
    
    # Optional Configuration
    freshdesk_domain: Optional[str] = Field(
        default=None,
        description="Freshdesk domain (e.g., yourcompany.freshdesk.com)"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Returns:
        Settings: Validated settings object with all configuration values
        
    Raises:
        ValidationError: If required environment variables are missing or invalid
    """
    return Settings()


# Project directory paths
PROJECT_ROOT = Path(__file__).parent.parent
CONTEXT_DIR = PROJECT_ROOT / "context"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_MARKDOWN_DIR = PROJECT_ROOT / "reports" / "markdown"
REPORTS_JSON_DIR = PROJECT_ROOT / "reports" / "json"
SRC_DIR = PROJECT_ROOT / "src"


def ensure_directories() -> None:
    """
    Ensure all required directories exist.
    Creates directories if they don't exist.
    """
    directories = [
        CONTEXT_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        REPORTS_MARKDOWN_DIR,
        REPORTS_JSON_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # Test configuration loading
    try:
        settings = get_settings()
        print("✓ Configuration loaded successfully")
        print(f"  - Freshdesk API Key: {'*' * 8}{settings.freshdesk_api_key[-4:]}")
        print(f"  - OpenAI API Key: {'*' * 8}{settings.openai_api_key[-4:]}")
        print(f"  - Log Level: {settings.log_level}")
        
        ensure_directories()
        print("✓ All directories verified/created")
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease ensure:")
        print("1. .env file exists in the project root")
        print("2. Required environment variables are set:")
        print("   - FRESHDESK_API_KEY")
        print("   - OPENAI_API_KEY")

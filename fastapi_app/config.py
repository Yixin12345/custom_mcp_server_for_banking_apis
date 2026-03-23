"""Configuration settings for FastAPI application."""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    app_name: str = "Custom MCP Server"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # FastAPI Server
    api_host: str = "127.0.0.1"
    api_port: int = 9000
    api_prefix: str = "/api/v1"
    
    # CORS
    cors_origins: list[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: list[str] = ["*"]
    
    class Config:
        """Settings config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

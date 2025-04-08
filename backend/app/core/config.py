import os
import secrets
from typing import List, Union, Optional, Any

from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator, field_validator


class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENCRYPTION_KEY: str = secrets.token_urlsafe(24)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Backend URL
    SERVER_NAME: str = "localhost"
    SERVER_HOST: AnyHttpUrl = "http://localhost:5000"
    SERVER_PORT: int = 5000
    
    # Debug mode
    DEBUG: bool = False
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Database
    DATABASE_URL: str = "sqlite:///./finance_app.db"
    
    # TrueLayer configuration
    TRUELAYER_CLIENT_ID: Optional[str] = None
    TRUELAYER_CLIENT_SECRET: Optional[str] = None
    TRUELAYER_REDIRECT_URI: str = "https://console.truelayer.com/redirect-page"
    TRUELAYER_PROVIDERS: str = "uk-ob-all uk-oauth-all"
    
    # Plaid configuration 
    PLAID_CLIENT_ID: Optional[str] = None
    PLAID_SECRET: Optional[str] = None
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Validate and assemble CORS origins."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("TRUELAYER_PROVIDERS", pre=True)
    def assemble_providers(cls, v: Union[str, List[str]]) -> str:
        """Validate and assemble TrueLayer providers."""
        if isinstance(v, list):
            return " ".join(v)
        return v
        
    @field_validator("DEBUG", mode="before")
    def parse_debug(cls, v: Any) -> bool:
        """Parse the DEBUG value to a boolean."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "t", "yes", "y")
        return False
    
    class Config:
        """Pydantic settings configuration."""
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost/focusflow"
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", alias="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", alias="ALGORITHM")


    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",   # LƯU Ý: alias UPPERCASE
    )

    DEBUG: bool = Field(default=True, alias="DEBUG")
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = Field(default=8000)
    
    # CORS - comma-separated list in environment variable
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    
    # Security
    TOKEN_EXPIRY_DAYS: int = 7
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
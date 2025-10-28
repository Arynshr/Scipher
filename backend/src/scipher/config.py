from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Set
import asyncio

class Settings(BaseSettings):
    APP_NAME: str = "Scipher API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./scipher.db"
    DB_ECHO: bool = False
    
    UPLOAD_DIR: Path = Path("uploads")
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: Set[str] = {".pdf"}
    
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    PROCESSING_TIMEOUT: int = 180
    
    PROCESSED_DATA_DIR: Path = Path("processed")
    TEMP_DIR: Path = Path("temp")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )
    
    async def initialize(self):
        """Asynchronously initialize settings and create directories"""
        # Validate critical settings
        if self.MAX_FILE_SIZE <= 0:
            raise ValueError("MAX_FILE_SIZE must be positive")
        if not self.ALLOWED_EXTENSIONS:
            raise ValueError("ALLOWED_EXTENSIONS cannot be empty")
        if self.PORT <= 0 or self.PORT > 65535:
            raise ValueError("PORT must be between 1 and 65535")
        
        # Create directories asynchronously
        try:
            loop = asyncio.get_event_loop()
            for directory in [self.UPLOAD_DIR, self.PROCESSED_DATA_DIR, self.TEMP_DIR]:
                await loop.run_in_executor(None, lambda: directory.mkdir(exist_ok=True))
        except Exception as e:
            raise ValueError(f"Failed to create required directories: {e}")

# Singleton instance
settings = Settings()

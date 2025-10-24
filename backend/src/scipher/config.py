from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Set

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
    
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]
    
    PROCESSING_TIMEOUT: int = 180
    
    PROCESSED_DATA_DIR: Path = Path("processed")
    TEMP_DIR: Path = Path("temp")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.PROCESSED_DATA_DIR.mkdir(exist_ok=True)
        self.TEMP_DIR.mkdir(exist_ok=True)


settings = Settings()

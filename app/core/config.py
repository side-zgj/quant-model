import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "QuantMonitor"
    API_V1_STR: str = "/api/v1"
    
    # Data Sources
    TUSHARE_TOKEN: str = os.getenv("TUSHARE_TOKEN", "")
    
    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        case_sensitive = True

settings = Settings()

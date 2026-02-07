import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379")
    redis_stream: str = "metrics:raw"
    redis_group: str = "ai_service_group"
    
    postgres_host: str = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    postgres_user: str = os.getenv("POSTGRES_USER", "kam_user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "kam_password")
    postgres_db: str = os.getenv("POSTGRES_DB", "kam_alerts")
    
    ollama_host: str = os.getenv("OLLAMA_HOST", "ollama")
    ollama_port: str = os.getenv("OLLAMA_PORT", "11434")
    
    model_path: str = "/app/models"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

def get_settings():
    return Settings()
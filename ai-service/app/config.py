import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379")
    redis_stream: str = "metrics:raw"
    redis_group: str = "ai_service_group"
    
    postgres_host: str = os.getenv("DB_HOST", "postgresql")
    postgres_port: str = os.getenv("DB_PORT", "5432")
    postgres_user: str = os.getenv("DB_USER", "enod_user")
    postgres_password: str = os.getenv("DB_PASSWORD", "enod_password")
    postgres_db: str = os.getenv("DB_NAME", "enod_alerts")
    
    ollama_host: str = os.getenv("OLLAMA_HOST", "ollama")
    ollama_port: str = os.getenv("OLLAMA_PORT", "11434")
    
    model_path: str = "/app/models/isolation_forest.joblib"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

def get_settings():
    return Settings()
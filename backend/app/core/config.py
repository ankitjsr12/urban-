from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'AI UrbanSense Central Backend'
    environment: str = 'development'
    database_url: str = 'postgresql+asyncpg://urbansense:urbansense@localhost:5432/urbansense'
    jwt_secret_key: str = 'change-this-in-production'
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 14
    redis_url: str = 'redis://localhost:6379/0'
    storage_provider: str = 'minio'
    s3_endpoint: str = 'http://localhost:9000'
    s3_access_key: str = 'minioadmin'
    s3_secret_key: str = 'minioadmin'
    s3_bucket: str = 'urbansense-evidence'
    s3_region: str = 'us-east-1'
    fcm_project_id: str | None = None
    fcm_credentials: str | None = None
    ai_service_url: str = 'http://localhost:8001'
    cors_origins: list[str] = [
        'http://localhost:3000',
        'http://localhost:5173',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173',
        'https://urbansense-api.onrender.com',
        'https://urbansense.onrender.com',
    ]
    rate_limit_per_minute: int = 120
    max_upload_bytes: int = 50 * 1024 * 1024
    anpr_min_verified_confidence: float = 0.85

    @field_validator('database_url', mode='before')
    @classmethod
    def fix_database_url(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith('postgres://'):
                return value.replace('postgres://', 'postgresql+asyncpg://', 1)
            if value.startswith('postgresql://') and not value.startswith('postgresql+asyncpg://'):
                return value.replace('postgresql://', 'postgresql+asyncpg://', 1)
        return value

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith('[') and value.endswith(']'):
                import json
                try:
                    return json.loads(value)
                except Exception:
                    pass
            return [origin.strip() for origin in value.split(',') if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

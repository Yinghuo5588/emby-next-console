from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    APP_NAME: str = "emby-next-api"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-to-a-long-random-string-at-least-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/emby_next"

    # Emby
    EMBY_HOST: str = "http://127.0.0.1:8096"
    EMBY_API_KEY: str = ""
    EMBY_DB_PATH: str = "/emby-data/playback_reporting.db"
    EMBY_DATA_MODE: str = "api"  # "api" | "sqlite" | "auto"
    EMBY_WEBHOOK_TOKEN: str = "embyconsole"
    DEFAULT_MAX_CONCURRENT: int = 2  # 默认并发限额

    # 观影生物钟时区偏移量（小时），相对于 UTC
    # 中国大陆: +8，日本: +9，美国西部: -8
    HEATMAP_TIMEZONE_OFFSET: int = 8

    # TMDB
    TMDB_API_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS - 支持逗号分隔（推荐）或 JSON 数组格式
    CORS_ORIGINS: str | list[str] = "http://localhost:5173"

    def get_cors_origins(self) -> list[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

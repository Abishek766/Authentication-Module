"""Application configuration loaded from environment variables.

Uses pydantic-settings for automatic .env file loading and type validation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Authentication Service.

    All fields without defaults are required and must be supplied via
    environment variables or the .env file.  Fields with defaults reflect
    production-ready values that are safe to use without override.
    """

    # --- Required secrets / infrastructure ---
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    JWT_SECRET_KEY: str

    # --- Security tuning ---
    BCRYPT_WORK_FACTOR: int = 12
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Application metadata ---
    APP_NAME: str = "Authentication Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


# Module-level singleton — import this throughout the codebase instead of
# instantiating Settings() multiple times.
settings = Settings()

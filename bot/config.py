from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    MAX_FILE_SIZE_MB: int = 20
    FREE_DAILY_LIMIT: int = 10
    TMP_DIR: str = "./tmp"
    DB_PATH: str = "./data/glasx.db"
    LOG_LEVEL: str = "INFO"
    ALLOWED_EXTENSIONS: str = (
        ".doc,.docx,.xls,.xlsx,.ppt,.pptx,.pdf,.jpg,.jpeg,.png,.webp,.heic"
    )
    TMP_MAX_AGE_SECONDS: int = 300

    @property
    def allowed_extensions_set(self) -> set[str]:
        return set(self.ALLOWED_EXTENSIONS.split(","))

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


config = Settings()

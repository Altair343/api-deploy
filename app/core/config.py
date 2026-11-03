from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL
from typing import Literal

class Settings(BaseSettings):
    APP_NAME: str = "My API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 10000
    REDIS_PASSWORD: str
    LOGIN_RATE_LIMIT_IP: int = Field(default=10, ge=1)
    LOGIN_RATE_LIMIT_ACCOUNT: int = Field(default=5, ge=1)
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=300, ge=1)

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_SSL_MODE: str =  "prefer" #"verify-full"
    DB_SSL_ROOT_CERT: str = "system"
    DB_POOL_SIZE: int = Field(default=5, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=5, ge=0)

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)

    APP_ENV: Literal["development", "test", "production"] = "development"
    PASSWORD_RESET_EXPIRE_MINUTES: int = Field(default=15,ge=1,le=60)
    PASSWORD_RESET_URL: str = ("http://localhost:3000/reset-password")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
            query={
                "sslmode": self.DB_SSL_MODE
                # "sslrootcert": self.DB_SSL_ROOT_CERT
            },
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()

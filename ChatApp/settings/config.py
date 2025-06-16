from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str

    ALGORITHM: str = "HS256"
    DATABASE_URL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

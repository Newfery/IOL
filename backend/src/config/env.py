from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    PORT: int = 8000
    JWT_SECRET: str
    PASSWORD_FINGERPRINT_SECRET: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()

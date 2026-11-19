from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    PORT: int = 8000
    JWT_SECRET: str
    PASSWORD_FINGERPRINT_SECRET: str | None = None
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:8080,http://127.0.0.1:8080"
    )

    class Config:
        env_file = ".env"


settings = Settings()

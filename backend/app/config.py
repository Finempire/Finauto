from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://finauto:finauto@localhost/finauto"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    TOKEN_EXPIRE_HOURS: int = 8
    ADMIN_EMAIL: str = "admin@finauto.com"
    ADMIN_PASSWORD: str = "admin123456"

    class Config:
        env_file = ".env"


settings = Settings()

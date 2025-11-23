
from dotenv import load_dotenv
load_dotenv()
import os
print(f"[DEBUG] DATABASE_URL from .env: {os.environ.get('DATABASE_URL')}")
from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./preppy.db"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60 * 24
    smtp_host: str = "localhost"
    smtp_user: str = "noreply@example.com"
    smtp_pass: str = "password"
    storage_bucket: str = "local"
    frontend_url: str = "https://preppynigga.com"
    barcode_base_url: str = "https://preppynigga.com/creator"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


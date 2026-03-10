import os
from pathlib import Path
from dotenv import load_dotenv

# Always load .env from project root (works regardless of current working directory)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "VQ System")
    ENV: str = os.getenv("ENV", "dev")
    DEBUG: bool = os.getenv("DEBUG", "1") in ("1", "true", "True", "yes", "on")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_TO_RANDOM_LONG_STRING")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./vq.db")

settings = Settings()

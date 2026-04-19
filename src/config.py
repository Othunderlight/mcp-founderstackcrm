import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings:
    # Django Backend
    DJANGO_BASE_URL: str = os.environ.get("DJANGO_BASE_URL", "http://127.0.0.1:8000")
    
    # Frontend URL (React app — used for OAuth2 login redirect)
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    # Server Port
    PORT: int = int(os.environ.get("PORT", 10000))

    BASE_DIR = Path(__file__).resolve().parent.parent

settings = Settings()
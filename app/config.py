import os

class AppConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    TZ = os.getenv("TZ", "America/Asuncion")

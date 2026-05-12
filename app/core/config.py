import os
from datetime import timedelta

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "7b9e6f3d1a2c4b5e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e") # Güçlü bir key kullanılmalı
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 saat

settings = Settings()

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "EdVentura"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/edventura"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    JWT_ALGORITHM: str = "RS256"
    JWT_PUBLIC_KEY: Optional[str] = None
    JWT_PRIVATE_KEY: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MEDIA_ROOT: str = "media"

    BCRYPT_ROUNDS: int = 12

    MFA_ISSUER: str = "EdVentura"

    SUPERADMIN_EMAIL: str = "admin@edventura.com"
    SUPERADMIN_PASSWORD: str = "changeme"


    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"

    # Email / SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "EdVentura"
    SMTP_FROM_EMAIL: str = ""
    SMTP_TLS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        base_dir = Path(__file__).resolve().parent.parent.parent
        priv_path = base_dir / "keys" / "private.pem"
        pub_path = base_dir / "keys" / "public.pem"
        if not self.JWT_PRIVATE_KEY and priv_path.exists():
            self.JWT_PRIVATE_KEY = priv_path.read_text()
        if not self.JWT_PUBLIC_KEY and pub_path.exists():
            self.JWT_PUBLIC_KEY = pub_path.read_text()

        # Fallback to HS256 if no RSA key is available
        if self.JWT_ALGORITHM.startswith("RS") and (not self.JWT_PRIVATE_KEY or "BEGIN " not in self.JWT_PRIVATE_KEY):
            self.JWT_ALGORITHM = "HS256"
            # SET THE SECRET – this line was missing!
            if not self.JWT_PRIVATE_KEY:
                self.JWT_PRIVATE_KEY = "edventura-hs256-fallback-secret-change-in-prod"
            self.JWT_PUBLIC_KEY = self.JWT_PRIVATE_KEY   # symmetric key

settings = Settings()
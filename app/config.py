"""
WDC App — Application Configuration
Loads environment variables and exposes a single `settings` object.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Firebase
    use_firebase: bool = False
    firebase_credentials_path: str = "./serviceAccountKey.json"
    firebase_api_key: str = ""
    firebase_auth_domain: str = ""
    firebase_project_id: str = ""
    firebase_storage_bucket: str = ""
    firebase_messaging_sender_id: str = ""
    firebase_app_id: str = ""

    # JWT
    jwt_secret: str = "wdc-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 12

    # Bootstrap admin
    default_super_admin_email: str = "admin@wdc.edu"
    default_super_admin_password: str = "Admin@123"

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "wdc-noreply@example.local"

    # CORS
    cors_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    poll_interval_seconds: int = 60
    database_url: str = "sqlite:///./resy_booker.db"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # JWT signing secret — set a long random string in production
    secret_key: str = "change-me-in-production"
    # Fernet encryption key for Resy credentials at rest.
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

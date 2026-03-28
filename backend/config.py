from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    resy_email: str = ""
    resy_password: str = ""
    resy_api_key: str = "VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"
    poll_interval_seconds: int = 60
    database_url: str = "sqlite:///./resy_booker.db"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

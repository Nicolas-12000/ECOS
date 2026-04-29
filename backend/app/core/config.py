from pathlib import Path
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    env: str = "dev"
    debug: bool = True
    database_url: str = ""
    db_user: str = ""
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = ""
    db_sslmode: str = ""
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if not (self.db_user and self.db_host and self.db_name):
            return ""
        user = quote(self.db_user)
        password = quote(self.db_password) if self.db_password else ""
        auth = f"{user}:{password}@" if password else f"{user}@"
        url = f"postgresql://{auth}{self.db_host}:{self.db_port}/{self.db_name}"
        if self.db_sslmode:
            url = f"{url}?sslmode={self.db_sslmode}"
        return url

    model_config = SettingsConfigDict(env_file=str(REPO_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore")


settings = Settings()

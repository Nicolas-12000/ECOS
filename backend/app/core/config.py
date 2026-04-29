from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "dev"
    debug: bool = True

    # Groq (LLM para RAG)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Supabase (opcional)
    supabase_url: str = ""
    supabase_anon_key: str = ""

    # Database (opcional — el backend funciona sin DB, con Parquet/CSV)
    database_url: str = ""
    supabase_db_url: str = ""

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def resolved_database_url(self) -> str | None:
        """Return the first available database URL, or None."""
        for url in [self.database_url, self.supabase_db_url]:
            if url:
                return url
        return None


settings = Settings()

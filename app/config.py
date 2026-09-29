from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "documents"
    postgres_user: str = "documents"
    postgres_password: str = "documents"

    elastic_url: str = "http://localhost:9200"
    elastic_index: str = "documents"

    search_result_limit: int = 20
    search_candidate_pool_size: int = 10_000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()

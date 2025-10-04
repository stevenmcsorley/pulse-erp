"""Configuration settings for Billing Service"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    postgres_db: str = "pulse_erp"
    postgres_user: str = "pulseadmin"
    postgres_password: str = "changeme"

    # NATS
    nats_url: str = "nats://localhost:4222"
    nats_stream: str = "orders"

    # Service
    service_name: str = "billing-service"
    service_port: int = 8003

    # Billing settings
    default_payment_terms_days: int = 30

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.db_host}:{self.db_port}/{self.postgres_db}"


settings = Settings()

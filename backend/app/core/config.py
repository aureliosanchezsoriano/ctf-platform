from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

# __file__ = .../backend/app/core/config.py
# parent 0 = .../backend/app/core
# parent 1 = .../backend/app
# parent 2 = .../backend
# parent 3 = project root (where .env lives)
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # Database
    database_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str

    # Redis
    redis_url: str

    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Flag engine
    flag_hmac_secret: str
    flag_prefix: str = "CTF"

    # Docker
    docker_socket: str = "/var/run/docker.sock"
    container_network_prefix: str = "ctf_user"

    # App
    environment: str = "development"
    allowed_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

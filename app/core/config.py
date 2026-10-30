from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# HS256 tokens are only as strong as the shared secret; 32 bytes (256 bits)
# is the minimum recommended by RFC 7518 for HMAC-SHA256.
JWT_SECRET_MIN_LENGTH = 32


class Settings(BaseSettings):
    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    @field_validator("jwt_secret_key")
    @classmethod
    def _check_secret_strength(cls, value: str) -> str:
        if len(value) < JWT_SECRET_MIN_LENGTH:
            raise ValueError(
                f"JWT_SECRET_KEY must be at least {JWT_SECRET_MIN_LENGTH} characters; "
                "generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
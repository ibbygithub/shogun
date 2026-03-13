from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    db_host: str = "192.168.71.221"
    db_port: int = 5432
    db_name: str = "shogun_v1"
    db_user: str = "shogun_app"
    db_password: str

    # Valkey
    valkey_host: str = "valkey.platform.ibbytech.com"
    valkey_port: int = 6379
    valkey_password: str

    # Platform services
    llm_gateway_url: str = "https://llm.platform.ibbytech.com"
    telegram_gateway_url: str = "http://platform-telegram-gateway:3001"
    telegram_send_secret: str

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8082
    log_level: str = "info"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

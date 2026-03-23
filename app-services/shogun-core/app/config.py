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
    telegram_bot_token: str        # Used to download voice/photo files from Telegram
    tavily_gateway_url: str = "https://tavily.platform.ibbytech.com"
    scraper_gateway_url: str = "https://scrape.platform.ibbytech.com"
    places_gateway_url: str = "http://192.168.71.220:8081"

    # Gemini direct REST — used for function-calling (llm-gateway doesn't support tool declarations)
    google_api_key: str = ""
    google_base_url: str = "https://generativelanguage.googleapis.com"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8082
    log_level: str = "info"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

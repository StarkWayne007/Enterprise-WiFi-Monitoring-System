from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    alert_email_recipient: str

    capture_interface: str = "eth0"
    capture_packet_count: int = 10
    capture_interval: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()

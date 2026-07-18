from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_secret_key: str
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 15
    database_url: str
    test_database_url: str | None = None
    queue_connection_string: str
    sms_queue_name: str = 'sms-verification-codes'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()

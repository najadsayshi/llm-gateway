from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    openai_api_base: str = "https://api.openai.com/v1"

    groq_api_key: str | None = None
    groq_api_base: str = "https://api.groq.com/openai/v1"

    openrouter_api_key: str | None = None
    openrouter_api_base: str = "https://openrouter.ai/api/v1"

    #POSTGRESQL DATABASE URL
    database_url : str
    

    request_timeout: float = 60.0

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

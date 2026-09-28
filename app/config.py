from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    openai_api_key : str
    openai_api_base : str = "https://api.openai.com/v1"
    request_timeout : float = 60.0

    model_config = SettingsConfigDict(
        env_file=".env")

    

settings = Settings()

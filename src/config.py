from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str = ""
    db_engine_url: str = "sqlite:///./ai_workflow_starter.sqlite"

    env: str = "dev"
    

settings = Settings()
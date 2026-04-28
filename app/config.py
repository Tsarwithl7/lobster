from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_model: str = "ollama/qwen2.5:7b-instruct-q4_K_M"
    ollama_base_url: str = "http://localhost:11434"
    db_path: str = "data/xia.db"
    secret_passphrase: str = "change-me"
    host: str = "127.0.0.1"
    port: int = 3008


settings = Settings()

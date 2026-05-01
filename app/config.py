from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_model: str = "Qwen/Qwen2.5-1.5B-Instruct"
    vllm_base_url: str = "http://localhost:8001"
    db_path: str = "data/xia.db"
    secret_passphrase: str = "change-me"
    host: str = "127.0.0.1"
    port: int = 3008


    redis_url: str = "redis://localhost:6379/0"
    embed_model: str = "BAAI/bge-m3"
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    embed_device: str = "cpu"
    semantic_cache_threshold: float = 0.92


settings = Settings()

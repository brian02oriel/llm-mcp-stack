from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"          # Ollama ignores it; Azure will use a real key
    llm_model: str = "qwen3:8b"
    mcp_url: str = "http://localhost:9000/mcp"
    max_tool_turns: int = 6
    disable_thinking: bool = True        # Qwen3-specific; set False for other models


settings = Settings()
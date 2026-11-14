from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Azure OpenAI (production) ---
    azure_endpoint: str | None = None            # https://<name>.openai.azure.com
    azure_deployment: str = "kpi-router"         # deployment name, NOT model name
    azure_api_version: str = "2024-10-21"
    azure_api_key: str | None = None             # unset when using managed identity

    # --- Ollama (local dev) ---
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen3:8b"
    disable_thinking: bool = True                # Qwen3 only; ignored on Azure

    mcp_url: str = "http://localhost:9000/mcp"
    max_tool_turns: int = 6
    max_output_tokens: int = 800

    @property
    def use_azure(self) -> bool:
        return bool(self.azure_endpoint)


settings = Settings()
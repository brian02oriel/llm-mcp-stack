from openai import AsyncAzureOpenAI, AsyncOpenAI

from config import settings


def build_llm_client() -> AsyncAzureOpenAI | AsyncOpenAI:
    """Return an Azure OpenAI client in the cloud, or a plain OpenAI-compatible
    client against Ollama locally. Both expose chat.completions.create with the
    same signature, so nothing downstream needs to know which it received.
    """
    if not settings.use_azure:
        return AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout=120.0,
            max_retries=3,
        )

    common = dict(
        azure_endpoint=settings.azure_endpoint,
        azure_deployment=settings.azure_deployment,
        api_version=settings.azure_api_version,
        timeout=60.0,
        max_retries=5,      # Azure returns 429 on TPM overrun; the SDK backs off
    )

    if settings.azure_api_key:
        return AsyncAzureOpenAI(api_key=settings.azure_api_key, **common)

    # Keyless: managed identity in Azure, `az login` session locally.
    from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    return AsyncAzureOpenAI(azure_ad_token_provider=token_provider, **common)


def model_arg() -> str:
    """`model` means deployment name on Azure, model tag on Ollama."""
    return settings.azure_deployment if settings.use_azure else settings.llm_model
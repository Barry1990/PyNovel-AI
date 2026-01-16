from .gemini import GeminiDriver
from .openai import OpenAIDriver

def get_driver(provider, api_key, model_name, base_url=None):
    provider = provider.lower()
    if provider == "gemini":
        return GeminiDriver(api_key, model_name, base_url)
    elif provider == "openai":
        return OpenAIDriver(api_key, model_name, base_url)
    else:
        raise ValueError(f"不支持的 Provider: {provider}")

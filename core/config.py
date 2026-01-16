import os
import yaml

def load_config(config_path="config.yaml"):
    if not os.path.exists(config_path):
        # 尝试读取 config.example.yaml 如果 config.yaml 不存在
        if os.path.exists("config.example.yaml"):
            with open("config.example.yaml", "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_api_key(config):
    provider = config.get("provider", "gemini").lower()
    config_api_key = config.get("api_key")
    env_var_name = "GEMINI_API_KEY" if provider == "gemini" else "OPENAI_API_KEY"
    env_api_key = os.getenv(env_var_name)

    if config_api_key and config_api_key.strip():
        return config_api_key
    return env_api_key

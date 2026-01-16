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

def select_config():
    """交互式选择配置文件"""
    yaml_files = [f for f in os.listdir('.') if f.endswith('.yaml') and f != 'config.example.yaml']
    
    if not yaml_files:
        print("未发现自定义配置文件，将使用默认模版 (config.example.yaml)")
        return load_config("config.example.yaml"), "config.example.yaml"

    print("\n--- 发现以下配置文件 ---")
    for i, f in enumerate(yaml_files, 1):
        print(f"{i}. {f}")
    
    try:
        choice = input(f"\n请选择配置文件编号 (默认 1, 直接回车确认): ").strip()
        idx = int(choice) - 1 if choice else 0
        if 0 <= idx < len(yaml_files):
            selected_file = yaml_files[idx]
            print(f"已选择: {selected_file}")
            return load_config(selected_file), selected_file
        else:
            print("选择无效，使用默认第一个。")
            return load_config(yaml_files[0]), yaml_files[0]
    except ValueError:
        return load_config(yaml_files[0]), yaml_files[0]

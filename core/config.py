import os
import yaml

def _load_env_from_file():
    """手动解析 .env 文件（防止用户没装 python-dotenv）"""
    # 寻找项目根目录下的 .env 文件
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env_path = os.path.join(root_dir, '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

# 启动时加载
_load_env_from_file()

# 尝试用专业的库再次覆盖（如果安装了的话）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def load_config(config_path="config.yaml"):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    configs_dir = os.path.join(root_dir, "configs")
    
    # 路径搜索优先级：
    # 1. 原始路径 (如果是绝对路径或相对当前目录存在)
    # 2. configs/ 目录下
    # 3. 根目录下
    search_paths = [
        config_path,
        os.path.join(configs_dir, config_path),
        os.path.join(root_dir, config_path)
    ]
    
    actual_path = None
    for p in search_paths:
        if os.path.exists(p) and os.path.isfile(p):
            actual_path = p
            break
            
    if not actual_path:
        # 兜底平衡：尝试在根目录下寻找备选的 config.example.yaml
        example_path = os.path.join(root_dir, "config.example.yaml")
        if os.path.exists(example_path):
            with open(example_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}
        
    with open(actual_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_api_key(config):
    provider = config.get("provider", "gemini").lower()
    
    # 按照用户要求，优先从环境变量获取
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        
    # 如果环境变量没有，再看配置文件是否有设置且不是占位符
    if not api_key:
        config_api_key = config.get("api_key")
        if config_api_key and config_api_key.strip() and config_api_key != "YOUR_API_KEY_HERE":
            api_key = config_api_key
            
    return api_key

def select_config():
    """交互式选择配置文件"""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    configs_dir = os.path.join(root_dir, "configs")
    
    # 优先从 configs/ 目录读取，如果没有则从根目录查找
    if os.path.exists(configs_dir):
        yaml_files = [f for f in os.listdir(configs_dir) if f.endswith('.yaml')]
        is_in_configs = True
    else:
        yaml_files = [f for f in os.listdir('.') if f.endswith('.yaml') and f != 'config.example.yaml']
        is_in_configs = False
    
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
            # 返回相对于 configs_dir 的路径或根路径
            if is_in_configs:
                return load_config(os.path.join("configs", selected_file)), selected_file
            else:
                return load_config(selected_file), selected_file
        else:
            print("选择无效，使用默认第一个。")
            default_file = yaml_files[0]
            if is_in_configs:
                return load_config(os.path.join("configs", default_file)), default_file
            else:
                return load_config(default_file), default_file
    except ValueError:
        default_file = yaml_files[0]
        if is_in_configs:
            return load_config(os.path.join("configs", default_file)), default_file
        else:
            return load_config(default_file), default_file

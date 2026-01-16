import sys
import os
import yaml
from core.config import load_config, get_api_key
from drivers.factory import get_driver

def generate_config_via_ai():
    # 1. 加载基础配置以初始化驱动
    base_config = load_config("config.example.yaml")
    provider = base_config.get("provider", "gemini").lower()
    api_key = get_api_key(base_config)
    
    if not api_key:
        print(f"请先在环境变量或 config.example.yaml 中设置 API Key 以运行生成器。")
        return

    model_name = base_config.get("model_name", "gemini-1.5-flash" if provider == "gemini" else "gpt-3.5-turbo")
    base_url = base_config.get("base_url")
    
    try:
        llm = get_driver(provider, api_key, model_name, base_url)
    except Exception as e:
        print(f"加载驱动失败: {e}")
        return

    # 2. 获取用户创意
    print("\n--- AI 配置文件生成器 ---")
    idea = input("请输入你的小说核心创意或简单描述: ").strip()
    if not idea:
        print("创意不能为空。")
        return

    # 3. 构造 Prompt
    with open("config.example.yaml", "r", encoding="utf-8") as f:
        template = f.read()

    prompt = f"""
你是一位资深的网络小说策划。请根据以下创意，生成一个完整的小说配置文件。
生成的格式必须严格遵守提供的 YAML 模板格式。

【小说创意】:
{idea}

【YAML 模板】:
{template}

【要求】:
1. 请根据创意构思一个吸引人的标题。
2. 详细填充 `details` 部分，包括女主、男主、反派的设定，背景冲突等。
3. 文风和基调要契合创意。
4. 只输出 YAML 内容，不要有任何 Markdown 包裹或其他解释文字。
"""

    print("正在通过 AI 构思配置文件，请稍候...")
    try:
        yaml_content = llm.generate_content(prompt)
        
        # 简单清理可能的 markdown 标签
        yaml_content = yaml_content.replace("```yaml", "").replace("```", "").strip()
        
        # 尝试验证 YAML 格式
        parsed = yaml.safe_load(yaml_content)
        
        # 4. 保存文件
        filename = f"config.{parsed['novel']['title']}.yaml".replace(" ", "_")
        # 移除非法文件名字符
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in "._-"]).strip()
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(yaml_content)
        
        print(f"\n生成成功！配置文件已保存至: {filename}")
        print("现在你可以运行 main.py 并选择这个文件来开始创作了。")
        
    except Exception as e:
        print(f"生成失败: {e}")

if __name__ == "__main__":
    generate_config_via_ai()

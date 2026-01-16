import sys
import os
import datetime

# 将项目根目录添加到 sys.path，确保可以导入 core 和 drivers 模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yaml
from core.config import load_config, get_api_key
from drivers.factory import get_driver

def generate_inspirations():
    # 1. 加载基础配置以初始化驱动
    # 假设 config.example.yaml 存在于项目根目录
    try:
        base_config = load_config("config.example.yaml")
    except Exception as e:
        print(f"读取 config.example.yaml 失败: {e}")
        # 尝试直接读取，如果 load_config 依赖 path
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        config_path = os.path.join(root_dir, "config.example.yaml")
        if os.path.exists(config_path):
             with open(config_path, 'r', encoding='utf-8') as f:
                base_config = yaml.safe_load(f)
        else:
             print("未找到 config.example.yaml，无法继续。")
             return

    provider = base_config.get("provider", "gemini").lower()
    api_key = get_api_key(base_config)
    
    if not api_key:
        env_vars = ["GEMINI_API_KEY", "GOOGLE_API_KEY"] if provider == "gemini" else ["OPENAI_API_KEY"]
        print(f"\n错误: 未找到 API Key。")
        print(f"已检查的环境变量: {', '.join(env_vars)}")
        print(f"也检查了 config.example.yaml 中的 'api_key' 字段。")
        return

    model_name = base_config.get("model_name", "gemini-1.5-flash" if provider == "gemini" else "gpt-3.5-turbo")
    base_url = base_config.get("base_url")
    
    try:
        llm = get_driver(provider, api_key, model_name, base_url)
    except Exception as e:
        print(f"加载驱动失败: {e}")
        return

    # 2. 获取用户输入
    print("\n--- AI 小说灵感生成器 ---")
    
    try:
        count_input = input("请输入要生成的灵感条数 (默认 5): ").strip()
        count = int(count_input) if count_input else 5
    except ValueError:
        print("输入无效，将生成默认 5 条。")
        count = 5

    topic_input = input("请输入偏好的题材 (如: 校园, 悬疑, 恋爱, 职场, 离职 等，留空则随机): ").strip()
    topic_desc = f"关于【{topic_input}】题材的" if topic_input else "各种随机题材（如校园、悬疑、恋爱、职场、离职等）的"

    # 3. 构造 Prompt
    prompt = f"""
你是一位资深的网络小说策划。请为我构思 {count} 个{topic_desc}小说灵感。

【要求】:
1. 灵感要有新意，避免过于俗套的剧情。
2. 题材可以多样化，或者专注于用户指定的方向。
3. 每个灵感请包含以下信息：
    - **标题**: 一个吸引人的暂定书名
    - **题材**: 如 都市/言情/悬疑/科幻 等
    - **核心梗**: 一句话描述最吸引人的点
    - **内容简介**: 100-200字左右的简要大纲，包含主角设定、主要冲突和预期看点。
4. 请用 Markdown 格式输出，每个灵感之间用分割线 `---` 隔开。
"""

    print("\n正在请求 AI 生成灵感，请稍候...")
    try:
        content = llm.generate_content(prompt)
        
        if content.startswith("⚠️"):
            print(f"\nLLM 生成失败: {content}")
            return

        # 4. 保存文件
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        inspirations_dir = os.path.join(root_dir, "inspirations")
        if not os.path.exists(inspirations_dir):
            os.makedirs(inspirations_dir)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inspirations_{timestamp}.md"
        save_path = os.path.join(inspirations_dir, filename)
        
        # 添加头部信息
        file_content = f"# 小说灵感生成\n\n- 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n- 关键词: {topic_input or '随机'}\n\n" + content
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        
        print(f"\n生成成功！灵感已保存至: {save_path}")
        print("\n--- 预览前 200 字符 ---")
        print(content[:200] + "...")
        
    except Exception as e:
        print(f"生成过程中发生错误: {e}")

if __name__ == "__main__":
    generate_inspirations()

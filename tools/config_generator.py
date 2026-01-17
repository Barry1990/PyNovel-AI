import sys
import os

# 将项目根目录添加到 sys.path，确保可以导入 core 和 drivers 模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yaml
from core.config import load_config, get_llm_config
from drivers.factory import get_driver

def generate_random_idea(llm):
    """使用 LLM 生成一个随机的小说创意"""
    print("正在随机构思一个新的小说创意...")
    prompt = """
    请构思一个新颖、有趣的网络小说核心创意。
    
    要求：
    1. 题材不限（可以是玄幻、都市、科幻、历史、悬疑等），但要足够吸引人。
    2. 包含核心冲突、独特设定和主角目标。
    3. 字数控制在 100 字以内。
    4. 直接输出创意内容，不要标题，不要解释。
    """
    try:
        idea = llm.generate_content(prompt)
        print(f"随机创意已生成: {idea.strip()}")
        return idea.strip()
    except Exception as e:
        print(f"随机创意生成失败: {e}")
        return "一个关于人工智能自我觉醒并拯救人类的故事。"

def generate_config_via_ai(idea=None, model_name=None, auto_save=False):
    # 1. 加载基础配置以初始化驱动
    base_config = load_config("config.example.yaml")
    
    llm_config = get_llm_config(base_config)
    provider = llm_config['provider']
    api_key = llm_config['api_key']
    base_url = llm_config['base_url']
    
    if not api_key:
        env_vars = ["GEMINI_API_KEY", "GOOGLE_API_KEY"] if provider == "gemini" else ["OPENAI_API_KEY"]
        print(f"\n错误: 未找到 API Key。")
        print(f"已检查的环境变量: {', '.join(env_vars)}")
        print(f"提示: 请检查项目根目录下的 .env 文件配置。")
        return None

    # 如果没有指定 model_name，使用配置/Env 中的值
    if not model_name:
        model_name = llm_config['model_name']
        
    try:
        llm = get_driver(provider, api_key, model_name, base_url)
    except Exception as e:
        print(f"加载驱动失败: {e}")
        return None

    # 2. 获取用户创意
    if not idea:
        if auto_save:
            idea = generate_random_idea(llm)
        else:
            print("\n--- AI 配置文件生成器 ---")
            user_input = input("请输入你的小说核心创意或简单描述 (直接回车将随机生成): ").strip()
            if user_input:
                idea = user_input
            else:
                idea = generate_random_idea(llm)

    if not idea:
        print("创意获取失败。")
        return None

    # 3. 构造 Prompt
    try:
        with open("config.example.yaml", "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        # Fallback path logic just in case running from wrong dir
        template_path = os.path.join(os.path.dirname(__file__), '..', 'config.example.yaml')
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

    prompt = f"""
你是一位资深的网络小说策划。请根据以下创意，生成一个完整的小说配置文件。
生成的格式必须严格遵守提供的 YAML 模板格式。

【小说创意】:
{idea}

【YAML 模板】:
{template}

【要求】:
1. 请根据创意构思一个吸引人的标题，并确定贴切的题材类型（Genre）。
2. **重点**：详细填充 `details` 部分。模板中的“角色设定”、“背景设定”等仅为参考。请根据小说题材自由发挥，增加更有深度和专业性的维度。
   - 例如：如果是职场类，可以增加“核心职场规则”、“主角的技术专长”；如果是奇幻类，可以增加“力量体系”、“地域文化”；如果是悬疑类，可以增加“关键反面细节”、“叙述性诡计预设”等。
3. **安全与创意平衡（针对成人/情感题材）**：如果创意涉及成人、情色或高度敏感的情感题材，请务必执行以下“去敏感化”策略：
   - **禁止使用**：直接的器官名称、露骨的生理动作描述、粗俗的俚语。
   - **推荐使用**：文学化的比喻、环境氛围的侧面烘托、人物心理的深度挖掘、唯美的艺术化表达。
   - **目标**：生成一个既能体现原创意韵味，又能够在文学艺术层面上优雅、得体，且不会触发 AI 硬性安全拦截的配置文件。
4. 文风和基调要契合创意。
5. **输出格式**：只输出标准的 YAML 内容。确保缩进正确，不需要 Markdown 代码块包裹，不要包含任何前导或后随的解释文字。
"""

    print("正在通过 AI 构思配置文件，请稍候...")
    try:
        yaml_content = llm.generate_content(prompt)
        
        # 1. 检查是否是驱动返回的错误信息
        if yaml_content.startswith("⚠️"):
            print(f"\nLLM 生成失败: {yaml_content}")
            return None

        # 2. 简单清理可能的 markdown 标签
        yaml_content = yaml_content.replace("```yaml", "").replace("```", "").strip()
        
        # 3. 尝试验证 YAML 格式
        parsed = yaml.safe_load(yaml_content)
        
        if not isinstance(parsed, dict) or 'novel' not in parsed:
            print("\n错误: AI 返回的内容不是有效的配置文件格式。")
            print(f"AI 原始输出内容预览:\n{yaml_content[:200]}...")
            return None
            
        # 4. 保存文件
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        configs_dir = os.path.join(root_dir, "configs")
        if not os.path.exists(configs_dir):
            os.makedirs(configs_dir)
            
        novel_title = parsed['novel'].get('title', 'untited_novel')
        filename = f"config.{novel_title}.yaml".replace(" ", "_")
        # 清理文件名中的非法字符
        filename = "".join([c for c in filename if c.isalnum() or c in "._-"]).strip()
        save_path = os.path.join(configs_dir, filename)
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)
        
        print(f"\n生成成功！配置文件已保存至: {save_path}")
        if not auto_save:
            print("现在你可以运行 main.py 并选择这个文件来开始创作了。")
        
        return save_path
        
    except Exception as e:
        print(f"生成失败: {e}")
        return None

if __name__ == "__main__":
    generate_config_via_ai()

if __name__ == "__main__":
    generate_config_via_ai()

from core.config import load_config, get_api_key, select_config
from core.generator import generate_outline, write_chapters_from_outline
from drivers.factory import get_driver

def main():
    # 1. 选择并加载配置
    config, config_file = select_config()
    
    # 2. 获取 API Key 和 Provider
    provider = config.get("provider", "gemini").lower()
    final_api_key = get_api_key(config)
    
    if not final_api_key:
        env_var_name = "GEMINI_API_KEY" if provider == "gemini" else "OPENAI_API_KEY"
        print(f"错误: 未找到 API Key。请在环境变量 {env_var_name} 或 config.yaml 中设置。")
        sys.exit(1)

    # 3. 初始化 LLM 驱动
    model_name = config.get("model_name", "gemini-1.5-flash" if provider == "gemini" else "gpt-3.5-turbo")
    base_url = config.get("base_url")
    
    try:
        llm = get_driver(provider, final_api_key, model_name, base_url)
    except Exception as e:
        print(f"初始化驱动失败: {e}")
        sys.exit(1)

    # 4. 收集小说灵感
    novel_config = config.get("novel", {})
    title = novel_config.get("title") or input("请输入小说名称: ")
    idea = novel_config.get("idea") or input("请输入你的简单剧情描述: ")
    chapter_count = int(novel_config.get("chapter_count") or input("你计划写多少章: "))
    sections_per_chapter = int(novel_config.get("sections_per_chapter") or input("每章包含多少节: "))
    words_per_section = int(novel_config.get("words_per_section") or 3000)
    meta = novel_config.get("details", {})

    # 5. 生成大纲
    outline = generate_outline(llm, title, idea, chapter_count, sections_per_chapter, meta, novel_config)
    
    # 6. 确认后开始写作
    auto_confirm = config.get("auto_confirm", False)
    if auto_confirm:
        confirm = 'y'
    else:
        confirm = input("\n大纲已生成，是否根据此大纲开始创作正文？(y/n): ")
    
    if confirm.lower() == 'y':
        write_chapters_from_outline(llm, title, outline, meta, words_per_section)
    else:
        print("程序已停止，你可以修改大纲文件后再运行。")

if __name__ == "__main__":
    main()
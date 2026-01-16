import google.generativeai as genai
import os
import re
import yaml

# --- 配置加载 ---
def load_config(config_path="config.yaml"):
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

GOOGLE_API_KEY = config.get("api_key", "YOUR_API_KEY_HERE")
MODEL_NAME = config.get("model_name", "gemini-3-flash-preview")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

def generate_outline(title, idea, chapter_count, sections_per_chapter, meta, novel_config):
    """阶段 1：根据用户描述生成详细大纲 (章->节 嵌套结构) - 迭代生成"""
    batch_size = novel_config.get("batch_size", 10)
    print(f"\n正在为你分阶段构思《{title}》的 {chapter_count} 章 (每章 {sections_per_chapter} 节) 大纲...")
    
    # 动态构建详细设定信息
    details_str = ""
    for category, fields in meta.items():
        details_str += f"\n【{category}】\n"
        if isinstance(fields, dict):
            for key, value in fields.items():
                details_str += f"{key}：{value}\n"
        else:
            details_str += f"{fields}\n"

    full_outline = ""
    history_context = "故事背景已由上述【基本信息】提供。"

    for start_chapter in range(1, chapter_count + 1, batch_size):
        end_chapter = min(start_chapter + batch_size - 1, chapter_count)
        print(f"正在生成第 {start_chapter} 章至第 {end_chapter} 章的大纲...")
        
        prompt = f"""
        你是一位资深的网文架构师和白金作家。
        
        【基本信息】
        小说题目：{title}
        核心创意：{idea}
        类型：{novel_config.get('genre', '未设定')}
        
        {details_str}
        
        【前阶段大纲回顾/背景】
        {history_context}
        
        任务：请为这个创意创作第 {start_chapter} 章至第 {end_chapter} 章的详细大纲（共 {end_chapter - start_chapter + 1} 章），每一章必须包含 {sections_per_chapter} 节。
        要求大纲逻辑严密，冲突密集，节奏紧凑，且必须与前文无缝衔接。
        
        格式要求：
        请严格按照以下格式输出，每章为一个标题，节缩进：
        第N章：[章标题/主要冲突]
          第M节：[本节具体情节描述]
        ...
        """
        
        response = model.generate_content(prompt)
        batch_outline = response.text
        full_outline += "\n" + batch_outline
        
        # 将当前批次的大纲作为下一批次的背景参考（简单截取末尾部分或全量，建议全量如果不太长）
        history_context = f"前 {end_chapter} 章大纲概要：\n" + batch_outline

    # 保存大纲文件
    with open(f"{title}_outline.md", "w", encoding="utf-8") as f:
        f.write(f"# 《{title}》分集大纲\n\n")
        f.write(full_outline)
    
    print(f"迭代大纲生成完毕，已保存至：{title}_outline.md")
    return full_outline

def write_chapters_from_outline(title, outline_text, meta, words_per_section):
    """阶段 2：读取嵌套大纲，按章建立文件夹，逐节创作"""
    if not os.path.exists(title):
        os.makedirs(title)

    # 动态构建详细背景信息
    details_str = ""
    for category, fields in meta.items():
        details_str += f"\n【{category}】\n"
        if isinstance(fields, dict):
            for key, value in fields.items():
                details_str += f"{key}：{value}\n"
        else:
            details_str += f"{fields}\n"

    history_summary = "故事刚开始。"
    
    # 简单解析大纲：获取章和节
    # 查找 "第X章" 及其后的节
    chapter_blocks = re.split(r"(第\d+章：.*)", outline_text)
    
    chapter_id = 0
    for block in chapter_blocks:
        if not block.strip():
            continue
            
        if block.startswith("第"):
            # 这是章标题头
            chapter_title = block.strip()
            chapter_id += 1
            chapter_dir = os.path.join(title, f"第{chapter_id:02d}章")
            if not os.path.exists(chapter_dir):
                os.makedirs(chapter_dir)
            continue
        
        # 这是章内的内容，包含节
        sections = re.findall(r"第\d+节：(.*)", block)
        for j, mission in enumerate(sections, 1):
            print(f"正在根据大纲创作 {chapter_title} - 第 {j} 节...")
            
            write_prompt = f"""
            你是一位白金级网络小说家。正在创作《{title}》。
            当前正在写：{chapter_title} 的第 {j} 节。
            
            【创作核心背景】
            {details_str}
            
            【前情回顾】：
            {history_summary}
            
            【本节任务】：
            本节大纲要求：{mission}
            
            {"【重要：黄金三章原则】目前处于小说开端，请务必在结尾留下巨大的悬念或转折，钩住读者继续阅读！" if chapter_id <= 3 else ""}
            
            【注意】：这是该小说的第 {chapter_id} 章第 {j} 节，请在内容中确保逻辑连贯。
            
            请展开细节，创作约 {words_per_section} 字的小说正文。要求：
            1. 保持文风一致，注重环境氛围描写和人物内心侧写。
            2. 对话自然，拒绝机械化的问答。
            3. 冲突处理要有张力，不要平铺直叙。
            """
            
            response = model.generate_content(write_prompt)
            content = response.text
            
            # 保存正文
            file_path = os.path.join(chapter_dir, f"第{j:02d}节.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            # 自动总结本节，作为下一节的记忆
            sum_resp = model.generate_content(f"请用300字总结本节（{chapter_title} 第{j}节）关键进展：\n{content}")
            history_summary = sum_resp.text
            print(f"第 {chapter_id} 章第 {j} 节完成。")

# --- 主程序入口 ---
if __name__ == "__main__":
    # 获取配置中的默认值
    novel_config = config.get("novel", {})
    
    # 第一步：收集你的灵感 (优先使用配置文件)
    title = novel_config.get("title") or input("请输入小说名称: ")
    idea = novel_config.get("idea") or input("请输入你的简单剧情描述: ")
    chapter_count = novel_config.get("chapter_count") or int(input("你计划写多少章: "))
    sections_per_chapter = novel_config.get("sections_per_chapter") or int(input("每章包含多少节: "))
    words_per_section = novel_config.get("words_per_section") or 3000
    genre = novel_config.get("genre") or input("请输入小说题材(如：仙侠、都市、悬疑): ")
    batch_size = novel_config.get("batch_size") or 10

    # 获取详细设定内容
    meta = novel_config.get("details", {})

    # 第二步：生成大纲
    outline = generate_outline(title, idea, chapter_count, sections_per_chapter, meta, novel_config)
    
    # 第三步：确认后开始写作
    auto_confirm = config.get("auto_confirm", False)
    if auto_confirm:
        confirm = 'y'
    else:
        confirm = input("\n大纲已生成，是否根据此大纲开始创作正文？(y/n): ")
    
    if confirm.lower() == 'y':
        write_chapters_from_outline(title, outline, meta, words_per_section)
    else:
        print("程序已停止，你可以修改大纲文件后再运行。")
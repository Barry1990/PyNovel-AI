import os
import re

def generate_outline(llm, title, idea, chapter_count, sections_per_chapter, meta, novel_config):
    """阶段 1：根据用户描述生成详细大纲"""
    batch_size = novel_config.get("batch_size", 10)
    print(f"\n正在为你分阶段构思《{title}》的 {chapter_count} 章 (每章 {sections_per_chapter} 节) 大纲...")
    
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
        
        【任务要求】
        1. 请为这个创意创作第 {start_chapter} 章至第 {end_chapter} 章的详细大纲（共 {end_chapter - start_chapter + 1} 章），每一章必须包含 {sections_per_chapter} 节。要求逻辑严密，冲突密集，节奏紧凑。
        
        2. **艺术化处理（重要）**：
           如果涉及敏感、成人或露骨情节，请务必使用**唯美、隐喻、文学化**的笔触。严禁使用直白的生理描写或粗俗词汇。通过环境描写、气氛烘托、角色的心理活动及极其克制且高级的暗示，来展现这种张力，确保内容的高级感且不触发安全机制。
        
        格式要求：
        请严格按照以下格式输出，每章为一个标题，节缩进：
        第N章：[章标题/主要冲突]
          第M节：[本节具体情节描述]
        ...
        """
        
        batch_outline = llm.generate_content(prompt)
        full_outline += "\n" + batch_outline
        history_context = f"前 {end_chapter} 章大纲概要：\n" + batch_outline

    with open(f"{title}_outline.md", "w", encoding="utf-8") as f:
        f.write(f"# 《{title}》分集大纲\n\n")
        f.write(full_outline)
    
    print(f"迭代大纲生成完毕，已保存至：{title}_outline.md")
    return full_outline

def write_chapters_from_outline(llm, title, outline_text, meta, words_per_section):
    """阶段 2：读取嵌套大纲，按章建立文件夹，逐节创作"""
    if not os.path.exists(title):
        os.makedirs(title)

    details_str = ""
    for category, fields in meta.items():
        details_str += f"\n【{category}】\n"
        if isinstance(fields, dict):
            for key, value in fields.items():
                details_str += f"{key}：{value}\n"
        else:
            details_str += f"{fields}\n"

    history_summary = "故事刚开始。"
    chapter_blocks = re.split(r"(第\d+章：.*)", outline_text)
    
    chapter_id = 0
    for block in chapter_blocks:
        if not block.strip():
            continue
            
        if block.startswith("第"):
            chapter_title = block.strip()
            chapter_id += 1
            chapter_dir = os.path.join(title, f"第{chapter_id:02d}章")
            if not os.path.exists(chapter_dir):
                os.makedirs(chapter_dir)
            continue
        
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
            4. **文学性要求（针对成人/情感内容）**：
               若情节涉及亲密接触或高度张力的场面，请采取**“侧面描写”**和**“艺术化修辞”**。
               - **推荐使用**：光影变换、角色急促的呼吸、汗水的晶莹、起伏的衣角、窗外的风雨等意象来侧面烘托。
               - **核心禁忌**：绝对禁止直接出现色情、暴力或任何违反安全准则的直白描写。通过这种“犹抱琵琶半遮面”的文学美感，在规避拦截的同时，提升作品的质感。
            """
            
            content = llm.generate_content(write_prompt)
            file_path = os.path.join(chapter_dir, f"第{j:02d}节.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            history_summary = llm.generate_content(f"请用300字总结本节（{chapter_title} 第{j}节）关键进展：\n{content}")
            print(f"第 {chapter_id} 章第 {j} 节完成。")

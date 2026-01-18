import os
import re

from core.state_manager import StateManager

def generate_outline(llm, title, idea, chapter_count, sections_per_chapter, meta, novel_config):
    """阶段 1：根据用户描述生成详细大纲"""
    outlines_dir = "outlines"
    if not os.path.exists(outlines_dir):
        os.makedirs(outlines_dir)
    
    outline_file = os.path.join(outlines_dir, f"{title}_outline.md")
    
    # 检查大纲是否已存在
    if os.path.exists(outline_file):
        print(f"\n检测到大纲文件已存在: {outline_file}")
        choice = input("是否直接使用已有大纲并进入创作阶段？(y: 使用已有 / n: 重新生成): ").strip().lower()
        if choice == 'y':
            with open(outline_file, "r", encoding="utf-8") as f:
                return f.read()

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

    # --- 新增步骤：生成全局剧情路标（Roadmap） ---
    print(f"\n正在构建全局剧情路标与伏笔埋设方案...")
    roadmap_system = "你是一位殿堂级的网文架构师。你的任务是构建宏大的故事架构，设计草蛇灰线的伏笔。"
    roadmap_prompt = f"""
        请根据以下核心创意，制定一份《全局剧情路标》。
        
        【小说题目】：{title}
        【核心创意】：{idea}
        
        【目标】：
        我们需要构建一个草蛇灰线、伏笔千里的宏大故事。请规划出：
        1. **核心故事曲线**（起、承、转、合 四个阶段的关键节点）。
        2. **全书终极悬念**（贯穿全书的最大谜题是什么）。
        3. **3-5 个关键伏笔方案**（具体的伏笔内容 + 预计揭秘时刻 + 建议在前期哪个阶段埋下）。
        
        请简练输出，不要废话。
    """
    try:
        global_roadmap = llm.generate_content(prompt=roadmap_prompt, system_instruction=roadmap_system)
        print("全局路标构建完成。")
        print("-" * 30)
        print(global_roadmap[:200] + "...")
        print("-" * 30)
    except Exception as e:
        print(f"⚠️ 全局路标生成失败: {e}，将跳过此步骤。")
        global_roadmap = "（无全局路标，常规生成）"

    full_outline = ""
    history_context = "故事背景已由上述【基本信息】提供。"

    for start_chapter in range(1, chapter_count + 1, batch_size):
        end_chapter = min(start_chapter + batch_size - 1, chapter_count)
        print(f"正在生成第 {start_chapter} 章至第 {end_chapter} 章的大纲...")
        
        outline_system = """你是一位资深的网文架构师和白金作家。

        你的任务是根据提供的背景和路标，创作详细的章节大纲。
        要求：
        1. 逻辑严密，冲突密集，节奏紧凑。
        2. **伏笔与悬念**：每一章开头明确标出【本章伏笔/悬念任务】。不仅要写情节，更要设计“钩子”。
        3. **艺术化处理（重要）**：如果涉及敏感、成人或露骨情节，请务必使用**唯美、隐喻、文学化**的笔触。严禁使用直白的生理描写或粗俗词汇。
        
        格式要求：
        请严格按照以下格式输出，每章为一个标题，节缩进：
        第N章：[章标题]
          【本章伏笔/悬念任务】：[简述本章需要埋设的伏笔或制造的悬念]
          第M节：[本节具体情节描述]
        ...
        """

        prompt = f"""
        【基本信息】
        小说题目：{title}
        核心创意：{idea}
        类型：{novel_config.get('genre', '未设定')}
        
        {details_str}
        
        【全局剧情路标 (时刻牢记)】
        {global_roadmap}
        
        【前阶段大纲回顾/背景】
        {history_context}
        
        【任务要求】
        请为这个创意创作第 {start_chapter} 章至第 {end_chapter} 章的详细大纲（共 {end_chapter - start_chapter + 1} 章），每一章必须包含 {sections_per_chapter} 节。
        """
        
        # ---------------------------------------------------------
        #  Retry Loop for Outline Generation (Safety Block Handling)
        # ---------------------------------------------------------
        max_retries = 3
        current_try = 0
        
        while current_try < max_retries:
            current_prompt = prompt
            if current_try > 0:
                print(f"🔄 [尝试 {current_try+1}/{max_retries}] 大纲生成触发安全拦截，正在切换至【唯美/隐喻模式】重试...")
                # Append strict safety guidelines to the prompt for the retry
                current_prompt += f"""
                
                【重要修正指令 ({current_try})】：
                检测到上一轮内容触发了安全审查（可能包含过于露骨的色情或暴力描述）。
                请立即调整写作策略：
                1. **彻底去敏感化**：严禁任何直接的性行为、器官描写或过度暴力。
                2. **使用文学隐喻**：用“潮汐”、“火焰”、“花朵”、“眼神交流”等意象代替直白描写。
                3. **侧重情感与氛围**：重点描写心理博弈和环境氛围，而非生理动作。
                请重新生成一段符合全年龄段安全标准的大纲。
                """

            batch_outline = llm.generate_content(prompt=current_prompt, system_instruction=outline_system)
            
            # If successful (no error marker), break the loop
            if not batch_outline.startswith("⚠️"):
                break
                
            print(f"⚠️ [失败] 尝试 {current_try+1} 仍被拦截: {batch_outline[:50]}...")
            current_try += 1
            
        # 检查是否在多次尝试后仍然失败
        if batch_outline.startswith("⚠️"):
            print(f"\n❌ [大纲生成失败] 第 {start_chapter} 章之后由于以下原因停止：")
            print(batch_outline)
            return None
            
        full_outline += "\n" + batch_outline
        history_context = f"前 {end_chapter} 章大纲概要：\n" + batch_outline

    with open(outline_file, "w", encoding="utf-8") as f:
        f.write(f"# 《{title}》分集大纲\n\n")
        f.write(f"## 全局剧情路标\n{global_roadmap}\n\n")
        f.write(full_outline)
    
    print(f"迭代大纲生成完毕，已保存至：{outline_file}")
    return full_outline

def sanitize_chapter_outline(llm, chapter_plan, error_msg):
    """
    当章节触发安全拦截时，尝试让 AI 重写该章节的大纲，使其更委婉、安全。
    """
    print(f"\n🔄 正在针对安全问题修正大纲...")
    print(f"\n🔄 正在针对安全问题修正大纲...")
    system_instruction = "你是一位经验丰富的网文编辑。你的任务是修正触发安全拦截的大纲片段，使其安全、委婉但保留核心剧情。"
    prompt = f"""
    【问题】：
    我们在根据以下大纲创作小说章节时，触发了 AI 的安全拦截机制（如色情、暴力等）。
    错误信息：{error_msg}
    
    【原大纲片段】：
    {chapter_plan}
    
    【任务】：
    请重写这段大纲。
    1. **保留核心剧情**：不要改变故事的走向和主要事件。
    2. **去敏感化**：
       - 将所有露骨、暴力、血腥或可能违规的描述，改为**隐喻、侧面描写**或**心理活动**。
       - 例如：将“激烈的打斗导致肢体横飞”改为“刀光剑影中，胜负已分，空气中弥漫着肃杀之气”。
       - 例如：将“亲密行为”改为“灯影摇曳，两颗心在此刻贴近”。
    3. **输出要求**：只输出修正后的大纲内容，不要解释。
    """
    try:
        new_plan = llm.generate_content(prompt=prompt, system_instruction=system_instruction)
        print("✅ 大纲修正完成。")
        return new_plan.strip()
    except Exception as e:
        print(f"⚠️ 大纲修正失败: {e}")
        return chapter_plan # 如果修正失败，只能返回原版尝试

def write_chapters_from_outline(llm, title, outline_text, meta, words_per_section):
    """阶段 2：读取嵌套大纲，按章建立文件夹，逐节创作"""
    if not os.path.exists(title):
        os.makedirs(title)

    # 初始化状态管理器
    state_manager = StateManager(title)

    details_str = ""
    for category, fields in meta.items():
        details_str += f"\n【{category}】\n"
        if isinstance(fields, dict):
            for key, value in fields.items():
                details_str += f"{key}：{value}\n"
        else:
            details_str += f"{fields}\n"

    chapter_blocks = re.split(r"(第\d+章：.*)", outline_text)
    
    chapter_id = 0
    chapter_title = ""
    chapter_dir = "" # 初始化防止报错

    for block in chapter_blocks:
        if not block.strip():
            continue
            
        # 章节标题行
        if block.strip().startswith("第") and "章：" in block:
            chapter_title = block.strip()
            chapter_id += 1
            chapter_dir = os.path.join(title, f"第{chapter_id:02d}章")
            if not os.path.exists(chapter_dir):
                os.makedirs(chapter_dir)
            continue
        
        # 章节内容块（包含"第N节"）
        sections = re.findall(r"第\d+节：(.*)", block)
        if not sections:
            continue

        if not chapter_dir:
            print(f"⚠️ 跳过无法归属章节的大纲片段: {block[:50]}...")
            continue

        current_chapter_plan = block.strip() # 提取本章的完整大纲内容作为局部上下文
        
        for j, mission in enumerate(sections, 1):
            file_path = os.path.join(chapter_dir, f"第{j:02d}节.txt")
            
            # 断点续传检查
            if os.path.exists(file_path):
                print(f"检测到 {chapter_title} - 第 {j} 节 已存在，自动跳过。")
                continue

            print(f"正在根据大纲创作 {chapter_title} - 第 {j} 节...")
            
            # 获取当前实时状态上下文 (Summary + Character State + Arcs + RAG Memory)
            # 使用当前章节大纲作为查询 query
            state_context = state_manager.get_context_prompt(llm=llm, current_query=current_chapter_plan)

            # --- Retry Loop for Safety/Content Blocks ---
            max_retries = 3
            current_try = 0
            
            while current_try < max_retries:
                write_system = f"""你是一位白金级网络小说家。正在创作《{title}》。
                
                【高级写作指令】：
                1. **执行伏笔埋设**：请仔细阅读【本章全局大纲】中的“伏笔/悬念任务”，自然地埋下伏笔。
                2. **黄金三章原则**：{"目前处于小说开端，请务必在结尾留下巨大的悬念或转折，钩住读者继续阅读！" if chapter_id <= 3 else "保持冲突的张力。"}
                3. **历史呼应**：巧妙呼应历史事件，增强连贯性。
                4. **文风要求**：注重环境氛围、人物内心。对话自然。
                5. **文学性要求（针对成人/情感内容）**：
                   若情节涉及亲密接触或高度张力的场面，请采取**“侧面描写”**和**“艺术化修辞”**（光影变换、呼吸、意象等）。
                   **核心禁忌**：绝对禁止直接出现色情、暴力或任何违反安全准则的直白描写。
                """
                
                write_prompt = f"""
                当前正在写：{chapter_title} 的第 {j} 节。
                
                【本章全局大纲与伏笔要求】：
                {current_chapter_plan}
                
                【重要：实时世界状态 & 历史记忆回溯】：
                {state_context}
                
                【创作核心背景】：
                {details_str}
                
                【本节任务】：
                本节大纲要求：{mission}
                
                【注意】：这是该小说的第 {chapter_id} 章第 {j} 节，请在内容中确保逻辑连贯。
                请展开细节，创作约 {words_per_section} 字的小说正文。
                """
                
                content = llm.generate_content(prompt=write_prompt, system_instruction=write_system)
                
                # 检查是否发生 LLM 错误 (Safety Block usually returns a specific message or empty)
                if content.startswith("⚠️"):
                    print(f"⚠️ [尝试 {current_try + 1}/{max_retries}] 创作触发安全/错误拦截: {content}")
                    
                    # 尝试修正大纲
                    new_plan = sanitize_chapter_outline(llm, current_chapter_plan, content)
                    if new_plan != current_chapter_plan:
                         current_chapter_plan = new_plan
                         print("🔄 应用修正后的本章大纲，重新尝试创作...")
                    
                    current_try += 1
                    continue # Retry loop
                else:
                    # Success
                    break
            
            # End of Retry Loop check
            if content.startswith("⚠️"):
                print(f"\n❌ [正文创作失败] {chapter_title} 第 {j} 节在 {max_retries} 次尝试后仍然失败。跳过本节。")
                content = f"（本节内容因反复触发安全策略生成失败，请人工介入补全。错误信息：{content}）"
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            # --- State Update ---
            # 使用 StateManager 更新全局摘要、角色状态和伏笔
            state_manager.update_state(llm, content)
                
            print(f"第 {chapter_id} 章第 {j} 节完成。")

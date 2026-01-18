import os
import yaml
from core.rag_engine import RAGEngine

class StateManager:
    def __init__(self, novel_dir):
        self.novel_dir = novel_dir
        self.global_summary_path = os.path.join(novel_dir, "global_summary.txt")
        self.character_state_path = os.path.join(novel_dir, "character_state.yaml")
        self.plot_arcs_path = os.path.join(novel_dir, "plot_arcs.yaml")
        
        self.rag = RAGEngine(novel_dir)
        self._init_files()

    def _init_files(self):
        """Initialize state files if they don't exist."""
        if not os.path.exists(self.novel_dir):
            os.makedirs(self.novel_dir)
            
        if not os.path.exists(self.global_summary_path):
            with open(self.global_summary_path, "w", encoding="utf-8") as f:
                f.write("故事刚刚开始。")
                
        if not os.path.exists(self.character_state_path):
            with open(self.character_state_path, "w", encoding="utf-8") as f:
                yaml.dump({}, f, allow_unicode=True)
                
        if not os.path.exists(self.plot_arcs_path):
            with open(self.plot_arcs_path, "w", encoding="utf-8") as f:
                yaml.dump({}, f, allow_unicode=True)

    def get_context_prompt(self, llm=None, current_query=None):
        """Build the context string for the generation prompt."""
        try:
            with open(self.global_summary_path, "r", encoding="utf-8") as f:
                summary = f.read()
                
            with open(self.character_state_path, "r", encoding="utf-8") as f:
                chars = f.read()
                
            with open(self.plot_arcs_path, "r", encoding="utf-8") as f:
                arcs = f.read()

            rag_context = ""
            if llm and current_query:
                # 尝试检索相关历史
                try:
                    query_vec = llm.embed_content(current_query)
                    if query_vec:
                        results = self.rag.search(query_vec, top_k=3)
                        if results:
                            rag_context = "\n【历史相关事件回溯】："
                            for i, doc in enumerate(results, 1):
                                rag_context += f"\n{i}. {doc['text']}"
                except Exception as e:
                    print(f"⚠️ RAG 检索失败 (非致命): {e}")
                
            context = f"""
【全局剧情摘要】：
{summary}

【角色当前状态】：
{chars}

【当前未解伏笔/剧情线】：
{arcs}
{rag_context}
            """
            return context
        except Exception as e:
            print(f"⚠️ 读取状态文件出错: {e}")
            return "（状态读取失败，请根据上文继续创作）"

    def update_state(self, llm, new_content):
        """Update all states based on the newly generated content."""
        print("  - 正在更新世界状态 (Summary/Characters/Arcs/Memory)...")
        
        # Read current states first
        current_context = self.get_context_prompt()
        
        prompt = f"""
        你是一个专业的网文辅助系统。请根据【最新生成的小说内容】，更新小说的状态数据库。
        
        【当前状态数据库】：
        {current_context}
        
        【最新生成的内容】：
        {new_content}
        
        【任务】：
        请分析最新内容，输出更新后的三个部分。
        1. **新的全局摘要**：将新内容整合进原摘要（保持由浅入深，不要无限变长，概括重点）。
        2. **角色状态更新**：如果文中提到了角色的新位置、受伤、获得物品、情绪变化等，请更新。输出格式为 YAML。
        3. **伏笔/剧情线更新**：
           - 如果有新挖的坑，添加进去。
           - 如果原有的坑填了，请移除或标记为[已解决]。
           - 输出格式为 YAML。
        4. **本节独立摘要（用于 RAG 记忆）**：
           - 单独输出一段 100 字左右的本节关键情节摘要，用于存入长期记忆库。
           
        【输出格式要求】：
        请严格使用以下格式分隔四个部分，不要输出多余的解释。
        **注意：YAML 中的所有字符串值，如果包含 []、-、: 等符号，请务必用英文双引号 " 包裹。**
        
        ===SUMMARY===
        (在此处更新全局摘要文本)
        ===CHARACTERS===
        (在此处更新角色状态 YAML)
        ===ARCS===
        (在此处更新剧情线 YAML)
        ===MEMORY===
        (在此处输出本节独立摘要)
        """
        
        try:
            response = llm.generate_content(prompt)
            self._parse_and_save_updates(llm, response)
        except Exception as e:
            print(f"⚠️ 状态更新失败: {e}")

    def _parse_and_save_updates(self, llm, response):
        """Parse the LLM response and save to files."""
        try:
            summary_content = ""
            chars_content = ""
            arcs_content = ""
            memory_content = ""
            
            # 简单的解析逻辑
            if "===SUMMARY===" in response:
                summary_content = response.split("===SUMMARY===")[1].split("===CHARACTERS===")[0].strip()
            
            if "===CHARACTERS===" in response:
                temp = response.split("===CHARACTERS===")[1]
                if "===ARCS===" in temp:
                    chars_content = temp.split("===ARCS===")[0].strip()
                    temp_arcs = temp.split("===ARCS===")[1]
                    
                    if "===MEMORY===" in temp_arcs:
                        arcs_content = temp_arcs.split("===MEMORY===")[0].strip()
                        memory_content = temp_arcs.split("===MEMORY===")[1].strip()
                    else:
                        arcs_content = temp_arcs.strip()
                else:
                    chars_content = temp.strip()
            
            # Save Summary
            if summary_content:
                with open(self.global_summary_path, "w", encoding="utf-8") as f:
                    f.write(summary_content)
            
            # Save Characters
            if chars_content:
                try:
                    clean_chars = self._sanitize_yaml(chars_content)
                    _ = yaml.safe_load(clean_chars) 
                    with open(self.character_state_path, "w", encoding="utf-8") as f:
                        f.write(clean_chars)
                except Exception as e:
                    print(f"⚠️ 角色状态YAML解析失败，已保存原始内容: {e}")
                    # 即使解析失败保存下来也比丢失好
                    with open(self.character_state_path, "w", encoding="utf-8") as f:
                        f.write(chars_content)

            # Save Arcs
            if arcs_content:
                try:
                    clean_arcs = self._sanitize_yaml(arcs_content)
                    _ = yaml.safe_load(clean_arcs)
                    with open(self.plot_arcs_path, "w", encoding="utf-8") as f:
                        f.write(clean_arcs)
                except Exception as e:
                    print(f"⚠️ 剧情线YAML解析失败，已保存原始内容: {e}")
                    with open(self.plot_arcs_path, "w", encoding="utf-8") as f:
                        f.write(arcs_content)
            
            # Save RAG Memory
            if memory_content:
                try:
                    vec = llm.embed_content(memory_content)
                    if vec:
                        self.rag.add_document(text=memory_content, vector=vec)
                        print("  * 已将本节摘要存入 RAG 长期记忆库。")
                except Exception as e:
                     print(f"⚠️ RAG 记忆存储失败: {e}")
                    
        except Exception as e:
            print(f"⚠️ 解析状态响应时发生错误: {e}")

    def _sanitize_yaml(self, text):
        """
        Attempts to clean and fix common YAML formatting errors from LLM output.
        """
        # 1. 去除 Markdown 代码块标记
        text = text.replace("```yaml", "").replace("```", "").strip()
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('#'):
                cleaned_lines.append(line)
                continue
                
            # 2. 尝试修复 `Key: Value` 中 Value 包含特殊符号（如 [], -）但未加引号的情况
            # 简单的 heuristic: 如果有一对冒号，且冒号后有内容，且内容没被引号包裹但包含特殊字符
            if ":" in line:
                key_part, val_part = line.split(":", 1)
                val_stripped = val_part.strip()
                
                # 如果 Value 不为空，且不是列表项开头(-)，且不以引号开头
                if val_stripped and not val_stripped.startswith("-") and not val_stripped.startswith('"') and not val_stripped.startswith("'"):
                    # 如果包含 YAML 敏感字符 (LIST start '[', MAPPING start '{', COMMENT '#', etc in value context)
                    # 为了安全起见，只要是以文本开头的，我们都尝试包裹引号（如果是纯数字/布尔值除外）
                    if any(c in val_stripped for c in "[]{}#:,"):
                         # 重新构建: 保持缩进 + key + : + "value"
                         # 注意要处理原 value 里的引号转义
                         safe_val = val_stripped.replace('"', '\\"')
                         line = f'{key_part}: "{safe_val}"'
            
            cleaned_lines.append(line)
            
        return "\n".join(cleaned_lines)

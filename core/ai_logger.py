import os
import datetime

def log_ai_interaction(prompt, response_text, usage_metadata=None):
    """
    记录 AI 交互日志到 logs/YYYYMMDD.log
    
    :param prompt: 发送给 AI 的提示词
    :param response_text: AI 返回的文本
    :param usage_metadata: (可选) Token 使用情况字典/对象
    """
    try:
        # 获取项目根目录
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        logs_dir = os.path.join(root_dir, "logs")
        
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(logs_dir, f"{today_str}.log")
        
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        usage_str = "Unknown"
        if usage_metadata:
             try:
                 # 兼容 Gemini 的 usage_metadata 对象
                 if hasattr(usage_metadata, 'prompt_token_count'):
                     p_tokens = usage_metadata.prompt_token_count
                     r_tokens = usage_metadata.candidates_token_count
                     t_tokens = usage_metadata.total_token_count
                     usage_str = f"Prompt: {p_tokens}, Response: {r_tokens}, Total: {t_tokens}"
                 # 兼容 OpenAI 的 usage 对象
                 elif hasattr(usage_metadata, 'prompt_tokens'):
                     p_tokens = usage_metadata.prompt_tokens
                     r_tokens = usage_metadata.completion_tokens
                     t_tokens = usage_metadata.total_tokens
                     usage_str = f"Prompt: {p_tokens}, Response: {r_tokens}, Total: {t_tokens}"
                 else:
                     usage_str = str(usage_metadata)
             except:
                 usage_str = str(usage_metadata)

        log_content = f"""
[{now_time}]
==================== REQUEST ====================
{prompt}

==================== RESPONSE ===================
{response_text}

==================== USAGE ======================
Tokens: {usage_str}
=================================================
"""
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_content)
            
    except Exception as e:
        print(f"⚠️ 日志记录失败: {e}")

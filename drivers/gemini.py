from .base import BaseDriver
import sys

class GeminiDriver(BaseDriver):
    def __init__(self, api_key, model_name, base_url=None):
        self.model_name = model_name
        try:
            import google.generativeai as genai
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            # 配置 API
            # 如果提供了 base_url (国内代理)，则通过 client_options 设置 api_endpoint
            if base_url:
                # 兼容性处理：如果用户填写的 URL 包含 http，则尝试提取或是直接使用
                # genai.configure 的 client_options 接受 api_endpoint
                genai.configure(api_key=api_key, client_options={'api_endpoint': base_url})
            else:
                genai.configure(api_key=api_key)
            
            # 默认安全设置：尽可能减少拦截，适合创意写作
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            self.model = genai.GenerativeModel(
                model_name=model_name,
                safety_settings=self.safety_settings
            )
        except ImportError:
            print("错误: 缺少 google-generativeai 库。请运行 'pip install google-generativeai'。")
            sys.exit(1)

    def generate_content(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            # 检查响应是否包含结果（有些情况下可能被安全过滤器完全拦截）
            if not response.candidates:
                return f"⚠️ [LLM 错误] 内容被安全拦截或生成失败。原因: {response.prompt_feedback}"
            
            return response.text
        except ValueError as e:
            # 处理 "The `response.parts` quick accessor requires a single candidate" 类似的错误
            return f"⚠️ [LLM 错误] 发生异常，可能是内容被拦截。详细信息: {str(e)}"
        except Exception as e:
            return f"⚠️ [LLM 错误] 未知异常: {str(e)}"

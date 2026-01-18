from .base import BaseDriver
import sys
from core.ai_logger import log_ai_interaction

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
            print("错误: 缺少 google-generativeai 库。请运行 'pip install google-generativeai' 进行安装。")
            sys.exit(1)

    def generate_content(self, prompt: str, system_instruction: str = None) -> str:
        try:
            # 如果提供了 system_instruction，我们需要重新实例化一个带有 instruction 的轻量级模型对象
            # 这是一个客户端操作，开销很小
            if system_instruction:
                import google.generativeai as genai
                current_model = genai.GenerativeModel(
                    model_name=self.model_name,
                    safety_settings=self.safety_settings,
                    system_instruction=system_instruction
                )
            else:
                current_model = self.model
            
            response = current_model.generate_content(prompt)
            # 检查响应是否包含结果（有些情况下可能被安全过滤器完全拦截）
            if not response.candidates:
                error_msg = f"⚠️ [LLM 错误] 内容被安全拦截或生成失败。原因: {response.prompt_feedback}"
                log_prompt = f"[System]: {system_instruction}\n[User]: {prompt}" if system_instruction else prompt
                log_ai_interaction(log_prompt, error_msg, getattr(response, 'usage_metadata', None))
                return error_msg
            
            text = response.text
            log_prompt = f"[System]: {system_instruction}\n[User]: {prompt}" if system_instruction else prompt
            log_ai_interaction(log_prompt, text, getattr(response, 'usage_metadata', None))
            return text
        except ValueError as e:
            # 处理 "The `response.parts` quick accessor requires a single candidate" 类似的错误
            # 翻译为中文提示
            return f"⚠️ [LLM 错误] 发生异常，可能是内容被拦截。原始错误: {str(e)}"
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                return f"⚠️ [LLM 错误] 找不到模型 '{self.model_name}' (404)。请检查 config.yaml 中的 model_name 是否正确，或代理是否支持该模型。"
    def embed_content(self, text: str) -> list[float]:
        try:
            import google.generativeai as genai
            # 使用 text-embedding-004 作为默认模型，这是一个很好的通用模型
            model = "models/text-embedding-004"
            result = genai.embed_content(
                model=model,
                content=text,
                task_type="retrieval_document", # 或者 retrieval_query，但在我们场景下 document 通用性更好
                title="Novel Context"
            )
            return result['embedding']
        except Exception as e:
            print(f"⚠️ [Embedding Error] Gemini 嵌入生成失败: {e}")
            return []

from .base import BaseDriver
import sys
from core.ai_logger import log_ai_interaction

class OpenAIDriver(BaseDriver):
    def __init__(self, api_key, model_name, base_url=None):
        self.model_name = model_name
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            print("错误: 缺少 openai 库。请运行 'pip install openai' 进行安装。")
            sys.exit(1)

    def generate_content(self, prompt: str, system_instruction: str = None) -> str:
        try:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            content = response.choices[0].message.content
            # Log with system instruction if present
            log_prompt = f"[System]: {system_instruction}\n[User]: {prompt}" if system_instruction else prompt
            log_ai_interaction(log_prompt, content, response.usage)
            return content
        except Exception as e:
            error_msg = f"⚠️ [OpenAI 错误] {str(e)}"
            log_ai_interaction(prompt, error_msg, None)
    def embed_content(self, text: str) -> list[float]:
        try:
            # 默认使用 text-embedding-3-small
            response = self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠️ [Embedding Error] OpenAI 嵌入生成失败: {e}")
            return []

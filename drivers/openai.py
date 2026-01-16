from .base import BaseDriver
import sys

class OpenAIDriver(BaseDriver):
    def __init__(self, api_key, model_name, base_url=None):
        self.model_name = model_name
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            print("错误: 缺少 openai 库。请运行 'pip install openai'。")
            sys.exit(1)

    def generate_content(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

from .base import BaseDriver
import sys

class GeminiDriver(BaseDriver):
    def __init__(self, api_key, model_name):
        self.model_name = model_name
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        except ImportError:
            print("错误: 缺少 google-generativeai 库。请运行 'pip install google-generativeai'。")
            sys.exit(1)

    def generate_content(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

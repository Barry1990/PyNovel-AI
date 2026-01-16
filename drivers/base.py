from abc import ABC, abstractmethod

class BaseDriver(ABC):
    @abstractmethod
    def generate_content(self, prompt: str) -> str:
        """生成文本内容的接口"""
        pass

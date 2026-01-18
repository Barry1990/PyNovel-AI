from abc import ABC, abstractmethod

class BaseDriver(ABC):
    @abstractmethod
    def generate_content(self, prompt: str) -> str:
        """生成文本内容的接口"""
        pass

    @abstractmethod
    def embed_content(self, text: str) -> list[float]:
        """生成文本嵌入向量的接口"""
        pass


import json
import os
import math

class RAGEngine:
    def __init__(self, novel_dir):
        self.novel_dir = novel_dir
        self.memory_file = os.path.join(novel_dir, "memory.json")
        self.documents = [] # List of {'text': str, 'vector': list[float], 'metadata': dict}
        self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
            except Exception as e:
                print(f"⚠️ 加载记忆文件失败: {e}")
                self.documents = []

    def save_memory(self):
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存记忆文件失败: {e}")

    def add_document(self, text, vector, metadata=None):
        if not vector:
            return
        
        doc = {
            "text": text,
            "vector": vector,
            "metadata": metadata or {}
        }
        self.documents.append(doc)
        self.save_memory()

    def search(self, query_vector, top_k=3):
        if not self.documents or not query_vector:
            return []

        results = []
        for doc in self.documents:
            score = self._cosine_similarity(query_vector, doc['vector'])
            results.append((score, doc))
        
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Return top_k documents
        return [item[1] for item in results[:top_k]]

    def _cosine_similarity(self, v1, v2):
        """Pure Python implementation of cosine similarity."""
        if len(v1) != len(v2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = math.sqrt(sum(a * a for a in v1))
        magnitude2 = math.sqrt(sum(b * b for b in v2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
            
        return dot_product / (magnitude1 * magnitude2)

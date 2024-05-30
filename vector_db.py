import numpy as np

class VectorDatabase:
    def __init__(self, dim):
        self.dim = dim
        self.data = []

    def add(self, embedding, text):
        self.data.append({'embedding': np.array(embedding), 'text': text})

    def search(self, query_embedding, top_k=5):
        query_embedding = np.array(query_embedding)
        similarities = []
        for item in self.data:
            similarity = np.dot(query_embedding, item['embedding']) / (np.linalg.norm(query_embedding) * np.linalg.norm(item['embedding']))
            similarities.append((similarity, item))
        similarities = sorted(similarities, key=lambda x: x[0], reverse=True)
        return [item for _, item in similarities[:top_k]]

from utils.vector_db import VectorDatabase
from utils.get_embeddings import get_embedding
from utils.gpt_query import get_query
from langchain_core.messages import HumanMessage, SystemMessage

class VillagerAgent:
    def __init__(self, agent_id, background_texts, dim=3072):
        self.agent_id = agent_id
        self.vector_db = VectorDatabase(dim)
        self.initialize_memory(background_texts)
    
    def initialize_memory(self, background_texts):
        for text in background_texts:
            self.add_to_memory(text, "system")

    def add_to_memory(self, text, person):
        embedding = get_embedding(f"{person}: {text}")
        self.vector_db.add(embedding, f"{person}: {text}")

    def generate_response(self, query):
        query_embedding = get_embedding(query)
        relevant_info = self.vector_db.search(query_embedding)
        context = " ".join([info['text'] for info in relevant_info])
        messages = [
            SystemMessage(content=context),
            HumanMessage(content=query)
        ]
        response = get_query(messages)
        return response

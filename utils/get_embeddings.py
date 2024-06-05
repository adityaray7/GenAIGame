from langchain_openai import AzureOpenAIEmbeddings
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
load_dotenv()
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import time
import requests


#open ai embeddings
def get_embedding(text, embedding_model="text-embedding3"):
  text = text.replace("\n", " ")
  start =time.time()
  embeddings = AzureOpenAIEmbeddings(
    azure_deployment=embedding_model
  )
  response = embeddings.embed_query(text)
  print(f"Time taken to get embeddings: {time.time()-start}")

  return response


#e5 embeddings
def get_e5_embedding(text):
  text = text.replace("\n", " ")
  start=time.time()
  model = SentenceTransformer('intfloat/e5-small')
  embeddings = model.encode(text)
  print(f"Time taken to get embeddings: {time.time()-start}")
  return embeddings

#e5 embeddings
if __name__ == "__main__":
  # print(get_e5_embedding("What is the meaning of life?"))

  emb1 = np.array(get_embedding("What is the meaning of life?")).reshape(-1,1)
  emb2 = get_e5_embedding("What is the meaning of life?").reshape(-1,1)

  similarity = cosine_similarity(emb1, emb2)[0][0]
  print(similarity)
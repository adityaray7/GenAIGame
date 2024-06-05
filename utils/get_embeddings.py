from langchain_openai import AzureOpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

def get_embedding(text, embedding_model="text-embedding3"):
  text = text.replace("\n", " ")
  embeddings = AzureOpenAIEmbeddings(
    azure_deployment=embedding_model
  )
  response = embeddings.embed_query(text)

  return response

if __name__ == "__main__":
  print(get_embedding("What is the meaning of life?"))
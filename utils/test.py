from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from pinecone import Pinecone, ServerlessSpec
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_pinecone import PineconeVectorStore
import faiss
import math
# from villager_description import villager_descriptions
from dotenv import load_dotenv
import os
from agentmemory import AgentMemory
from agent import Agent

load_dotenv("../.env")

ATLAS_CONNECTION_STRING=os.getenv("ATLAS_CONNECTION_STRING")

# Connect to your Atlas cluster
client = MongoClient(ATLAS_CONNECTION_STRING)

# Define collection and index name
db_name = "langchain_db"
collection_name = "test"
atlas_collection = client[db_name][collection_name]
vector_search_index = "vector_index"


villager_descriptions = [
    ["I am George. I enjoy exploring the woods and gathering herbs. I often cook meals for my fellow villagers."],
    ["I am Thomas. I have a knack for construction and enjoy building structures. I believe a sturdy village is key to our safety."],
    ["I am Henry. I am always on high alert, watching over the village day and night. I take pride in keeping everyone safe from harm."]
    # ["I am Villager 3.", "I am drawn to the river, where I find peace and serenity.", "I am the one who fetches water for the village."],
    # ["I am Villager 4.", "I am passionate about culinary arts and experimenting with flavors.", "I love to create delicious meals for my friends and family."],
    # ["I am Villager 5.", "I am a skilled hunter, trained to track and capture prey.", "I provide meat and hides to sustain our community."],
    # ["I am Villager 6.", "I am curious by nature and enjoy exploring new territories.", "I often venture into the unknown to gather information."],
    # ["I am Villager 7.", "I have a strong connection to nature and spend my days gathering wood and tending to the forest.", "I ensure we have enough resources to thrive."],
    # ["I am Villager 8.", "I possess knowledge of ancient healing techniques passed down through generations.", "I am the village healer, tending to the sick and injured."],
    # ["I am Villager 9.", "I am patient and compassionate, with a gift for teaching.", "I educate the children of our village, guiding them toward a brighter future."],
]

os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

llm = AzureChatOpenAI(
    azure_deployment="GPT35-turboA",
    api_version="2024-02-01",
    temperature=0
)

def relevance_score_fn(score: float) -> float:
    """Return a similarity score on a scale [0, 1]."""
    # This will differ depending on a few things:
    # - the distance / similarity metric used by the VectorStore
    # - the scale of your embeddings (OpenAI's are unit norm. Many others are not!)
    # This function converts the euclidean norm of normalized embeddings
    # (0 is most similar, sqrt(2) most dissimilar)
    # to a similarity function (0 to 1)
    

    # this returns negetive relevance values so temporarily made abs()
    # change this to implement cosine_similarity
    return abs(1.0 - (score / math.sqrt(2)))

def create_new_memory_retriever():
    """Create a new vector store retriever unique to the agent."""
    # Define your embedding model
    embeddings_model = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding3",
        api_version="2024-02-01"
    )
    # Initialize the vectorstore as empty
    embedding_size = 3072

    ###############################################
    # index = faiss.IndexFlatL2(embedding_size)
    vectorstore = MongoDBAtlasVectorSearch(atlas_collection, embeddings_model)
    
    # vectorstore = FAISS(
    #     embedding_function=embeddings_model,
    #     index=index,
    #     docstore=InMemoryDocstore({}),
    #     index_to_docstore_id={},
    #     relevance_score_fn=relevance_score_fn,
    # )
    return TimeWeightedVectorStoreRetriever(
        vectorstore=vectorstore, other_score_keys=["importance"], k=15, decay_rate=0.005
    )

george_memory = AgentMemory(
    llm=llm,
    memory_retriever=create_new_memory_retriever(),
)

george = Agent(
    name="George",
    llm=llm,
    description=villager_descriptions[0],
    status="Herb Specialist",
    memory=george_memory,
)

thomas_memory = AgentMemory(
    llm=llm,
    memory_retriever=create_new_memory_retriever()
)

thomas = Agent(
    name="Thomas",
    llm=llm,
    description=villager_descriptions[1],
    status="Construction worker",
    memory=thomas_memory
)

USER_NAME = "Samarth"

def interview_agent(agent: Agent, message: str) -> str:
    """Help the notebook user interact with the agent."""
    print(message)
    new_message = f"{USER_NAME} says {message}. If you don't know the answer, say that you don't know."
    return agent.generate_dialogue_response(new_message)[1]

# def run_conversation(agents: List[Agent], initial_observation: str) -> None:
    """Runs a conversation between agents."""
    print(initial_observation)
    _, observation = agents[1].generate_reaction(initial_observation)
    print(observation)
    turns = 0
    counter = 0
    while True and counter < 10:
        break_dialogue = False
        for agent in agents:
            stay_in_dialogue, observation = agent.generate_dialogue_response(
                observation
            )
            print(observation)
            # observation = f"{agent.name} said {reaction}"
            if not stay_in_dialogue:
                break_dialogue = True
        if break_dialogue:
            break
        turns += 1
        counter += 1

print(interview_agent(george, "What do you do?"))

# george_memory.add_memory(memory_content="I heard from someone that there are lot of medicinal herbs near pond.")

# Returns list of Document objects stored in the memory
# print(george.memory.memory_retriever.memory_stream)

# Document metadata consists 'importance' score, 'last_accessed_at' time and 'created_at' time

# Returns list of strings stored in the agent's memory
# print([document.page_content for document in george.memory.memory_retriever.memory_stream])

print(interview_agent(george, "What is thomas' occupation?"))

agents = [george, thomas]
# run_conversation(
#     agents,
#     "George: Hi, Thomas. What have you been upto lately? What is your occupation?",
# )

# print(interview_agent(george, "What is thomas' occupation?"))
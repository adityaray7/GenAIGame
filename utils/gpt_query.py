from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
load_dotenv()

def get_query(messages, max_tokens=100, temperature=0.0, deployment_name="GPT35-turboA"):
    model = AzureChatOpenAI(
        deployment_name=deployment_name,
        temperature=temperature,
        max_tokens=max_tokens
    )
    response = model.invoke(messages)
    return response.content
   
if __name__ == "__main__":
    print(get_query([
        HumanMessage(content="What is the meaning of life?"),
        SystemMessage(content="The meaning of life is to live and learn. Output only this and nothing else. DO NOT OUTPUT ANYTHING ELSE.")
    ]))
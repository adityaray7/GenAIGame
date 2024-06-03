import openai
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv(".env")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_API_ENDPOINT")
)

# def get_query(messages,model = 'GPT35-turboA'):
#     response = client.chat.completions.create(
#         model=model, # model = "deployment_name".
#         messages=messages
#     )
#     return response.choices[0].message.content
   

def get_gpt_3_5_turbo_response(prompt):
    response = client.chat.completions.create(
        model="GPT35-turboA",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response

def calculate_cost(response):
    usage = response.usage
    total_tokens = usage.total_tokens
    print(f"Total tokens: {total_tokens}")
    cost_per_1k_tokens = 0.002  # for example purposes

    cost = (total_tokens / 1000) * cost_per_1k_tokens
    return cost

prompt = "Explain the theory of relativity."
response = get_gpt_3_5_turbo_response(prompt)
print(response.choices[0].message.content)

cost = calculate_cost(response)
print(f"Total cost: ${cost:.4f}")

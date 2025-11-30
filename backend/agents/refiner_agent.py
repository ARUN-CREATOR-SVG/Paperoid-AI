from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
import os
from dotenv import load_dotenv

load_dotenv()

model = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    task="text-generation",
    temperature=0.4,
    max_new_tokens=512,
    huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
)
llm = ChatHuggingFace(llm=model)

def refiner_agent(draft: str):
    """Refine the final version"""
    prompt = f"Refine and improve this draft to make it sound academic and coherent:\n\n{draft}"
    return llm.invoke(prompt).content

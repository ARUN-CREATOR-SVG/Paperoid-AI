from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
import os
from dotenv import load_dotenv

load_dotenv()

model_endpoint = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    task="text-generation",
    temperature=0.7,          
    max_new_tokens=512,     
    top_p=0.9,               
    return_full_text=False, 
    huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
)

llm = ChatHuggingFace(llm=model_endpoint)



def retriever_agent(topic: str):
    """
    Retrieves relevant research papers and converts them into Citation-compatible dicts.
    """
    prompt = f"""
You are a helpful research assistant. 
List exactly 5 recent research papers related to:
'{topic}'

Format each line as:
Title: <paper title> - Summary: <2 lines>
"""

    try:
        response = llm.invoke(prompt)
        text = response.content

        papers = []
        for i, line in enumerate(text.split("\n")):
            if line.strip():
                if " - " in line:
                    title, summary = line.split(" - ", 1)
                else:
                    title, summary = line, ""
                
                papers.append({
                    "title": title.replace('Title:', '').strip(),
                    "summary": summary.replace('Summary:', '').strip(),
                    "key": f"[Ref-{i+1}]",
                    "source_id": f"src-{i+1}"
                })

        if not papers:
            papers = [{
                "title": "No papers found",
                "summary": "Model returned empty response.",
                "key": "[Ref-1]",
                "source_id": "src-1"
            }]

        return papers

    except Exception as e:
        print(f"❌ Retriever error: {e}")
        return [{
            "title": "Retrieval failed",
            "summary": f"Error: {e}",
            "key": "[Ref-Error]",
            "source_id": "src-error"
        }]
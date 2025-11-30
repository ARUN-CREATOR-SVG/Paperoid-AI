from tools.arxiv_tool import search_arxiv
import os
from dotenv import load_dotenv

load_dotenv()


def retriever_agent(topic: str, limit: int = 10):
    """
    Retrieves relevant research papers from arXiv and converts them into Citation-compatible dicts.
    """
    print(f"🔍 Searching arXiv for: {topic} (Limit: {limit})")
    try:
        # Fetch real papers from arXiv
        results = search_arxiv(topic, max_results=limit)
        print(f"✅ Found {len(results)} papers from arXiv API.")
        
        papers = []
        for i, p in enumerate(results):
            # Clean up summary to be single line for better context injection
            clean_summary = p["summary"].replace("\n", " ").strip()
            
            papers.append({
                "title": p["title"],
                "summary": clean_summary,
                "key": f"[Ref-{i+1}]",
                "source_id": p["link"],
                "link": p["link"],
                "pdf": p["pdf"]
            })
            
        if not papers:
             print(f"⚠️ No relevant papers found for '{topic}' after filtering.")
             return [{
                "title": "No relevant research papers found",
                "summary": f"No papers matching '{topic}' were found on arXiv. The topic might be too specific or fictional.",
                "key": "[Ref-None]",
                "source_id": "N/A",
                "link": "N/A",
                "pdf": "N/A"
            }]
            
        return papers

    except Exception as e:
        print(f"❌ Retriever error: {e}")
        return [{
            "title": "Retrieval failed",
            "summary": f"Error: {str(e)}",
            "key": "[Ref-Error]",
            "source_id": "src-error"
        }]
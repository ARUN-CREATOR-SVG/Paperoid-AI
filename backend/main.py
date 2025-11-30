from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from schemas.paper_schemas import PaperoidState, ResearchRequest
from workflow.research_graph import stream_research_graph
from tools.arxiv_tool import search_arxiv, calculate_similarity
from pydantic import BaseModel
import os
import json


app = FastAPI(
    title="Paperoid Research Paper Generator",
    description="AI-powered backend to generate structured research papers using LLaMA 3",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "🚀 Paperoid Research Paper Generator is running!"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "paperoid-api"}

@app.post("/generate-paper/")
async def generate_paper(request: ResearchRequest):
    """
    Generate a research paper based on the provided request.
    Returns a streaming response with progress updates.
    """
    state = PaperoidState(request=request)
    
    def event_generator():
        for update in stream_research_graph(state):
            yield json.dumps(update) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


class PlagiarismRequest(BaseModel):
    title: str
    abstract: str


@app.post("/check-plagiarism/")
async def check_plagiarism(request: PlagiarismRequest):
    """
    Check for potential plagiarism (similarity) against arXiv papers.
    """
    try:
        # Helper to extract keywords (simple stopword removal)
        def extract_keywords(text):
            stopwords = {"a", "an", "the", "in", "on", "of", "for", "and", "or", "with", "to", "at", "by", "is", "are", "was", "were", "this", "that", "it", "from", "as", "be", "study", "paper", "research", "analysis", "survey", "review", "comprehensive", "proposed", "using", "based"}
            words = text.lower().replace("-", " ").split()
            keywords = [w for w in words if w.isalnum() and w not in stopwords and len(w) > 2]
            return " ".join(keywords[:6]) # Return top 6 keywords

        # 1. Search arXiv using keywords from Title
        search_query = extract_keywords(request.title)
        if not search_query:
            search_query = request.title # Fallback to raw title if keywords fail

        search_results = search_arxiv(search_query, max_results=10)
        
        # Fallback: If no results found, try keywords from Abstract
        if not search_results:
             fallback_query = extract_keywords(request.abstract)
             if fallback_query:
                search_results = search_arxiv(fallback_query, max_results=10)
        
        similar_papers = []
        
        if search_results:
            for paper in search_results:
                # 2. Calculate similarity between abstracts
                paper_summary = paper.get("summary", "")
                # Use Jaccard similarity (Word Overlap)
                similarity_score = calculate_similarity(request.abstract, paper_summary)
                
                # Convert to percentage
                score_percent = round(similarity_score * 100, 2)
                
                similar_papers.append({
                    "title": paper.get("title"),
                    "link": paper.get("link"),
                    "pdf": paper.get("pdf"),
                    "similarity_score": score_percent,
                    "summary": paper_summary[:200] + "..." # Truncate for display
                })
                
            # Sort by similarity score descending
            similar_papers.sort(key=lambda x: x["similarity_score"], reverse=True)
            # Keep top 5
            similar_papers = similar_papers[:5]

        # Calculate overall plagiarism score (Max of individual scores)
        overall_score = 0.0
        if similar_papers:
            overall_score = max(p["similarity_score"] for p in similar_papers)
            
        return {
            "similar_papers": similar_papers,
            "overall_score": overall_score
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking plagiarism: {str(e)}")


@app.get("/download-pdf/{job_id}")
async def download_pdf(job_id: str):
    """
    Download the generated PDF by job_id.
    """
    output_dir = "output"
    pdf_path = None
    
    # Search for the PDF file with matching job_id
    for filename in os.listdir(output_dir):
        if filename.startswith(f"paper_{job_id}") and filename.endswith(".pdf"):
            pdf_path = os.path.join(output_dir, filename)
            break
    
    if pdf_path and os.path.exists(pdf_path):
        return FileResponse(
            pdf_path, 
            media_type="application/pdf",
            filename=f"research_paper_{job_id}.pdf"
        )
    else:
        raise HTTPException(status_code=404, detail="PDF not found")
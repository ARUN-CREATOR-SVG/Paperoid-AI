from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from schemas.paper_schemas import PaperoidState, ResearchRequest
from workflow.research_graph import run_research_graph
import os


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
    """
    try:
        state = PaperoidState(request=request)
        
        final_state = run_research_graph(state)

        #  Extract data safely from either dict or PaperoidState
        if isinstance(final_state, dict):
            job_id = final_state.get("job_id")
            title = final_state.get("title")
            abstract = final_state.get("abstract")
            status = final_state.get("status")
            pdf_path = final_state.get("output_pdf")
            generation_time = final_state.get("generation_time_s")
            sections = final_state.get("sections", [])
            references = final_state.get("references", [])
        else:
            job_id = getattr(final_state, "job_id", None)
            title = getattr(final_state, "title", None) or getattr(final_state, "draft_title", None)
            abstract = getattr(final_state, "abstract", None)
            status = getattr(final_state, "status", None)
            pdf_path = getattr(final_state, "output_pdf", None)
            generation_time = getattr(final_state, "generation_time_s", None)
            sections = getattr(final_state, "sections", [])
            references = getattr(final_state, "references", [])

        if status == "FAILED":
            raise HTTPException(
                status_code=500, 
                detail=f"Paper generation failed: {getattr(final_state, 'errors', ['Unknown error'])}"
            )

        return {
            "job_id": job_id,
            "title": title or "Untitled Research Paper",
            "abstract": abstract or "No abstract available.",
            "status": status or "COMPLETED",
            "pdf_path": pdf_path,
            "generation_time": round(generation_time, 2) if generation_time else 0,
            "num_sections": len(sections),
            "num_references": len(references)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating paper: {str(e)}")


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
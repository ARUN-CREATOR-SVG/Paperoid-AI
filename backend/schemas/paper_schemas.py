from typing import List, Optional
from pydantic import BaseModel, Field

# --- User Input ---

class ResearchRequest(BaseModel):
    """
    User request for starting research paper generation.
    """
    title: Optional[str] = Field(None, description="Title of the research paper (optional).")
    topic_or_prompt: str = Field(..., description="Main topic or question for the research paper.")
    word_count: int = Field(5000, description="Approximate total word count for the paper.")
    num_references: int = Field(10, description="Minimum number of references to include.")


# --- Documents and References ---

class SourceDocument(BaseModel):
    """
    One document collected from the web or database.
    """
    source_url: str = Field(..., description="URL or ID of the source.")
    title: str = Field(..., description="Title of the source document.")
    content_snippet: str = Field(..., description="Important part of the document used in generation.")


class Citation(BaseModel):
    """
    One reference or citation in the paper.
    """
    key: str = Field(..., description="Short in-text key (e.g., [Smith et al., 2023]).")
    entry: str = Field(..., description="Full reference in APA/MLA format.")
    source_id: str = Field(..., description="Links this citation to its source document.")


# --- Paper Sections ---

class PaperSection(BaseModel):
    """
    A section of the research paper (like Introduction, Methodology, etc.).
    """
    section_title: str = Field(..., description="Section title.")
    content: str = Field(..., description="Generated content for this section.")


# --- LangGraph State (during generation) ---

class PaperoidState(BaseModel):
    """
    Tracks data while the paper is being generated.
    """
    request: ResearchRequest
    documents: List[SourceDocument] = Field(default_factory=list)
    sections: List[PaperSection] = Field(default_factory=list)
    references: List[Citation] = Field(default_factory=list)
    draft_title: Optional[str] = None
    abstract: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True
        extra = 'allow'



class ResearchPaper(BaseModel):
    """
    The final research paper after generation is complete.
    """
    job_id: str = Field(..., description="Unique ID for the paper generation job.")
    title: str = Field(..., description="Final paper title.")
    abstract: str = Field(..., description="Short summary of the paper.")
    sections: List[PaperSection] = Field(..., description="All sections of the paper in order.")
    references: List[Citation] = Field(..., description="List of references used.")
    generation_time_s: float = Field(..., description="Time taken to generate the paper (in seconds).")
    status: str = Field("COMPLETED", description="Final status of the paper generation.")

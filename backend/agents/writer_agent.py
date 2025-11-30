from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from schemas.paper_schemas import PaperSection
import os
from dotenv import load_dotenv
from typing import List, Tuple

load_dotenv()

def get_writer_model(page_length: int):
    """Return a Hugging Face model endpoint based on paper size."""
    repo = "meta-llama/Meta-Llama-3-8B-Instruct"
    max_tokens = 512 if page_length <= 5 else 1024

    return HuggingFaceEndpoint(
        repo_id=repo,
        task="text-generation",
        temperature=0.7,
        max_new_tokens=max_tokens,
        top_p=0.9,
        return_full_text=False,
        huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
    )


# Simple writer for short papers (3–4 pages)
def writer_agent(topic: str, references: list, page_length: int = 5) -> Tuple[str, List[PaperSection]]:
    """Generate a compact research paper (used for short papers)."""

    llm = ChatHuggingFace(llm=get_writer_model(page_length))
    ref_text = "\n".join(references[:5])

    prompt = f"""
You are an academic researcher.
Write a detailed research paper on the topic "{topic}".
Include these sections:
1. Title
2. Abstract
3. Introduction
4. Methodology
5. Results and Discussion
6. Conclusion
7. References (APA style, at least 5)

Use these references for inspiration:
{references}

Target: around {page_length} pages.
"""


    response = llm.invoke(prompt)
    content = response.content.strip()

    title = "Untitled Research Paper"
    if "Title:" in content:
        title_line = content.split("\n")[0]
        title = title_line.replace("Title:", "").strip()

    sections = [PaperSection(section_title="Full Paper", content=content)]

    return title, sections


# Iterative writer for longer, detailed papers
def writer_agent_iterative(topic: str, references: list, page_length: int = 5) -> Tuple[str, List[PaperSection]]:
    """
    Generate research paper section-by-section for higher quality and full structure.
    """
    llm = ChatHuggingFace(llm=get_writer_model(page_length))
    ref_text = "\n".join([f"{i+1}. {ref}" for i, ref in enumerate(references[:10])])

    # 🧩 Generate Title
    title_prompt = f"Generate an academic research paper title for '{topic}'. Respond with only the title."
    title_response = llm.invoke(title_prompt)
    title = title_response.content.strip().replace("Title:", "").replace("**", "")

    sections = []

    # 🎯 Section Templates 
    section_prompts = [
        ("Abstract", f"Write a 200-word academic abstract for '{topic}'. Include purpose, method, results, and conclusion."),
        ("Introduction", f"Write an Introduction (400–500 words) explaining background, motivation, research objectives, and problem statement for '{topic}'."),
        ("Literature Review", f"Write a Literature Review (400–500 words) summarizing 3–5 previous studies related to '{topic}', using these references:\n{ref_text}"),
        ("Methodology", f"Write a Methodology (300–400 words) describing data sources, tools, algorithms, and evaluation metrics used for '{topic}'."),
        ("Results and Discussion", f"Write a Results & Discussion section (500–600 words) presenting outcomes, insights, and critical analysis of '{topic}'."),
        ("Conclusion", f"Write a Conclusion (250–300 words) summarizing main findings, limitations, and future scope for '{topic}'."),
        ("References", f"Write at least 5 references in APA format based on:\n{ref_text}")
    ]

    # ⚙️ Loop through all sections
    for name, prompt in section_prompts:
        try:
            print(f"🧠 Generating section: {name}")
            response = llm.invoke(prompt)
            content = response.content.strip()

            # 🧹 Clean text (avoid duplicate headers)
            content = content.replace("**", "")
            content = content.replace("Title:", "").replace("Abstract:", "").strip()

            sections.append(PaperSection(section_title=name, content=content))
        except Exception as e:
            sections.append(PaperSection(section_title=name, content=f"⚠️ Error generating {name}: {e}"))

    # ✅ Return final structured paper
    return title or f"Research on {topic}", sections


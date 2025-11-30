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
def writer_agent(topic: str, context: list, page_length: int = 5) -> Tuple[str, List[PaperSection]]:
    """Generate a Survey Paper / Literature Review based on retrieved abstracts."""

    llm = ChatHuggingFace(llm=get_writer_model(page_length))
    # Join the context list into a single string
    context_text = "\n\n".join(context)

    prompt = f"""
You are an academic researcher.
Write a detailed research paper on the topic "{topic}".

Use the following retrieved research papers as the PRIMARY SOURCE of information. 
Do NOT hallucinate. Base your Abstract, Introduction, Methodology, and Results on these facts.
Synthesize the methods and results found in these papers.

CONTEXT (Retrieved Papers):
{context_text}

Include these sections:
1. Title
2. Abstract (Must summarize the provided context)
3. Introduction
4. Literature Review
5. Methodology (Synthesize methods from the retrieved papers)
6. Results and Discussion (Synthesize findings from the retrieved papers)
7. Conclusion
8. References (List the titles from the context)

Target: around {page_length} pages.
"""

    response = llm.invoke(prompt)
    content = response.content.strip()

    title = f"A Survey of {topic}"
    if "Title:" in content:
        title_line = content.split("\n")[0]
        title = title_line.replace("Title:", "").strip()

    sections = [PaperSection(section_title="Survey Paper", content=content)]

    return title, sections


# Iterative writer for longer, detailed papers
def writer_agent_iterative(topic: str, context: list, page_length: int = 5) -> Tuple[str, List[PaperSection]]:
    """
    Generate a structured Survey Paper section-by-section.
    """
    llm = ChatHuggingFace(llm=get_writer_model(page_length))
    # Join the context list into a single string
    context_text = "\n\n".join(context)

    # 🧩 Generate Title
    title = f"A Comprehensive Survey of {topic}"

    sections = []

    # 🎯 Section Templates 
    section_prompts = [
        ("Abstract", f"Write a 200-word academic abstract for '{topic}'. It MUST strictly summarize the findings from the following retrieved papers:\n{context_text}"),
        ("Introduction", f"Write an Introduction (400–500 words) for '{topic}'. Use the following context to explain the background and problem statement. Do NOT invent facts:\n{context_text}"),
        ("Literature Review", f"Write a Literature Review (400–500 words) synthesizing the following specific studies. Cite them by title:\n{context_text}"),
        ("Methodology", f"Write a Methodology (300–400 words) describing the research methods used in the retrieved papers. Synthesize their approaches (e.g., datasets, algorithms, experimental setups) based ONLY on the provided context:\n{context_text}"),
        ("Results and Discussion", f"Write a Results & Discussion section (500–600 words) synthesizing the key findings and results reported in the retrieved papers. Discuss the implications of these results. Do NOT invent new results:\n{context_text}"),
        ("Conclusion", f"Write a Conclusion (250–300 words) summarizing the collective findings from the provided context:\n{context_text}"),
        ("References", f"List the references exactly as they appear in the provided context:\n{context_text}")
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
    return title, sections


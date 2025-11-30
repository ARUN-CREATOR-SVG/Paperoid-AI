import os
from datetime import datetime
from fpdf import FPDF
from schemas.paper_schemas import PaperSection, Citation


def render_latex_pdf(
    title: str,
    abstract: str,
    sections: list[PaperSection],
    references: list[Citation] = None,
    output_dir: str = "output"
):
    """
    Generates a structured PDF file with the given title, abstract, and sections.
    Returns metadata for frontend display.
    """
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"paper_{timestamp}.pdf")

    pdf = FPDF()
    pdf.add_page()

    # --- Clean text helper ---
    def clean_text(text):
        return text.encode("latin-1", "replace").decode("latin-1")

    # --- Title ---
    pdf.set_font("Arial", "B", 18)
    pdf.multi_cell(0, 10, clean_text(title), align="C")
    pdf.ln(10)

    # --- Abstract ---
    pdf.set_font("Arial", "I", 12)
    pdf.multi_cell(0, 10, f"Abstract:\n{clean_text(abstract)}")
    pdf.ln(10)

    # --- Sections ---
    for section in sections:
        # Skip if the section is the Abstract (since we already printed it)
        clean_title = section.section_title.strip().lower().replace("*", "")
        if "abstract" in clean_title and len(clean_title) < 15:
            continue
        # Skip if the section is References (since we print it manually at the end)
        if "reference" in clean_title or "bibliography" in clean_title:
             continue

        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 10, clean_text(section.section_title))
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, clean_text(section.content))
        pdf.ln(8)

    # --- References Section ---
    if references:
        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 10, "References")
        pdf.set_font("Arial", "", 12)
        for i, ref in enumerate(references, 1):
            ref_entry = f"[{i}] {ref.entry}"
            pdf.multi_cell(0, 8, clean_text(ref_entry))
        pdf.ln(10)

    pdf.output(output_path)

    return {
        "job_id": timestamp,
        "title": title,
        "abstract": abstract[:300] + "..." if len(abstract) > 300 else abstract,
        "status": "Completed",
        "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pdf_path": output_path
    }

from langgraph.graph import StateGraph, START, END
from schemas.paper_schemas import PaperoidState, SourceDocument, Citation
from agents.retriever_agent import retriever_agent
from agents.writer_agent import writer_agent, writer_agent_iterative
from agents.refiner_agent import refiner_agent
from tools.write_pdf import render_latex_pdf
import time, uuid


def retrieve_node(state: PaperoidState) -> dict:
    """Step 1: Retrieve related research papers and generate reference list."""
    print("\n📚 Retrieving related research papers...")

    papers = retriever_agent(state.request.topic_or_prompt)

    state.documents = [
        SourceDocument(
            source_url="N/A",
            title=p.get("title", "Untitled Paper"),
            content_snippet=p.get("summary", "")
        )
        for p in papers
    ]

    state.references = [
        Citation(
            key=p.get("key", f"[Ref-{i+1}]"),
            entry=f"{p.get('title', 'Untitled')} - {p.get('summary', '')}",
            source_id=p.get("source_id", f"source_{i+1}")
        )
        for i, p in enumerate(papers)
    ]

    print(f"✅ Retrieved {len(state.references)} references.\n")
    return {"documents": state.documents, "references": state.references}



def write_node(state: PaperoidState) -> dict:
    """Step 2: Generate research paper sections using references."""
    print("✍️ Writing paper draft...")

    try:
        if state.request.page_length >= 5:
            title, draft_sections = writer_agent_iterative(
                state.request.topic_or_prompt,
                [r.entry for r in state.references],
                page_length=state.request.page_length
            )
        else:
            title, draft_sections = writer_agent(
                state.request.topic_or_prompt,
                [r.entry for r in state.references],
                page_length=state.request.page_length
            )

        state.draft_title = title or f"Research on {state.request.topic_or_prompt}"
        state.sections = draft_sections
        state.draft_text = "\n\n".join([s.content for s in draft_sections])
        state.abstract = (
            draft_sections[0].content[:500] if draft_sections else "No abstract generated."
        )

        print(f"✅ Draft written with {len(draft_sections)} sections.\n")
        return {
            "draft_title": state.draft_title,
            "sections": state.sections,
            "draft_text": state.draft_text,
            "abstract": state.abstract,
        }

    except Exception as e:
        print(f"❌ Error during writing stage: {e}")
        state.errors.append(str(e))
        return {"errors": state.errors}


def refine_node(state: PaperoidState) -> dict:
    """Step 3: Refine and enhance generated draft."""
    print("🔧 Refining content for clarity and academic tone...")

    try:
        refined_text = refiner_agent(state.draft_text or "")
        state.final_text = refined_text or state.draft_text
        if not state.abstract:
            state.abstract = refined_text[:400]
        print("✅ Refinement complete.\n")

        return {"abstract": state.abstract, "final_text": state.final_text}

    except Exception as e:
        print(f"❌ Refinement error: {e}")
        state.errors.append(str(e))
        return {"errors": state.errors}


def pdf_node(state: PaperoidState) -> dict:
    """Step 4: Generate formatted PDF output."""
    print("📄 Generating final PDF...")

    try:
        output_data = render_latex_pdf(
            title=state.draft_title or state.request.topic_or_prompt,
            abstract=state.abstract or "No abstract available.",
            sections=state.sections,
        )

        
        state.output_pdf = output_data.get("pdf_path")
        state.job_id = output_data.get("job_id", uuid.uuid4().hex)
        state.title = output_data.get("title", state.draft_title)
        state.status = output_data.get("status", "COMPLETED")
        state.generation_time_s = round(time.time() - (state.start_time or time.time()), 2)

        print(f"✅ PDF generated successfully at: {state.output_pdf}\n")

        return {
            "output_pdf": state.output_pdf,
            "job_id": state.job_id,
            "generation_time_s": state.generation_time_s,
            "status": state.status,
            "title": state.title,
        }

    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        state.errors.append(str(e))
        return {"errors": state.errors}



def build_research_graph():
    """Builds the complete LangGraph workflow for research generation."""
    graph = StateGraph(PaperoidState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("write", write_node)
    graph.add_node("refine", refine_node)
    graph.add_node("pdf", pdf_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "write")
    graph.add_edge("write", "refine")
    graph.add_edge("refine", "pdf")
    graph.add_edge("pdf", END)

    return graph.compile()


def run_research_graph(state: PaperoidState) -> PaperoidState:
    """Executes the entire paper generation pipeline."""
    state.start_time = time.time()
    print(f"\n🚀 Starting generation for: {state.request.topic_or_prompt}\n")

    compiled_graph = build_research_graph()

    try:
        final_state = compiled_graph.invoke(state)

        if isinstance(final_state, dict):
            for k, v in final_state.items():
                if hasattr(state, k):
                    setattr(state, k, v)

        state.status = state.status or "COMPLETED"
        state.generation_time_s = round(time.time() - state.start_time, 2)

        print(f"🏁 Research generation complete in {state.generation_time_s} sec.\n")
        return state

    except Exception as e:
        print(f"💥 Workflow crashed: {e}")
        state.status = "FAILED"
        state.errors.append(str(e))
        return state

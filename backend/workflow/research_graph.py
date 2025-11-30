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

    papers = retriever_agent(state.request.topic_or_prompt, limit=state.request.num_references)

    # Check if retrieval failed or found no relevant papers
    if len(papers) == 1 and papers[0].get("key") == "[Ref-None]":
        error_msg = papers[0].get("summary", "No relevant papers found.")
        print(f"⛔ {error_msg}")
        # We raise an exception to stop the graph execution and notify the frontend
        raise ValueError(f"Retrieval Error: {error_msg}")

    state.documents = [
        SourceDocument(
            source_url=p.get("link", "N/A"),
            title=p.get("title", "Untitled Paper"),
            content_snippet=p.get("summary", "")
        )
        for p in papers
    ]

    state.references = [
        Citation(
            key=p.get("key", f"[Ref-{i+1}]"),
            entry=f"{p.get('title', 'Untitled')} (Source: {p.get('link', 'N/A')})",
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
        # Prepare rich context for the writer (Title + Summary)
        context_list = [
            f"Title: {doc.title}\nSummary: {doc.content_snippet}\nSource: {doc.source_url}"
            for doc in state.documents
        ]

        if state.request.page_length >= 5:
            title, draft_sections = writer_agent_iterative(
                state.request.topic_or_prompt,
                context_list,
                page_length=state.request.page_length
            )
        else:
            title, draft_sections = writer_agent(
                state.request.topic_or_prompt,
                context_list,
                page_length=state.request.page_length
            )

        state.draft_title = title or f"Research on {state.request.topic_or_prompt}"
        state.sections = draft_sections
        state.draft_text = "\n\n".join([s.content for s in draft_sections])
        # Find the abstract section
        abstract_section = next((s for s in draft_sections if s.section_title.lower() == "abstract"), None)
        if abstract_section:
            state.abstract = abstract_section.content
        else:
            state.abstract = draft_sections[0].content[:500] if draft_sections else "No abstract generated."

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
        if not state.abstract or state.abstract == "No abstract generated.":
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
            references=state.references
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
            "abstract": state.abstract, # Return abstract to ensure it's captured
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


def stream_research_graph(state: PaperoidState):
    """Executes the pipeline and yields status updates."""
    state.start_time = time.time()
    yield {"type": "log", "message": f"🚀 Starting generation for: {state.request.topic_or_prompt}"}

    compiled_graph = build_research_graph()

    try:
        # We use .stream() to get updates from each node
        # stream_mode="updates" returns the output of the node that just finished
        for output in compiled_graph.stream(state):
            for node_name, node_output in output.items():
                if node_name == "retrieve":
                    count = len(node_output.get("references", []))
                    yield {"type": "log", "message": f"📚 Retrieved {count} references."}
                    # Update state
                    state.references = node_output.get("references", [])
                    state.documents = node_output.get("documents", [])
                    
                elif node_name == "write":
                    count = len(node_output.get("sections", []))
                    yield {"type": "log", "message": f"✍️ Draft written with {count} sections."}
                    # Update state
                    state.sections = node_output.get("sections", [])
                    state.abstract = node_output.get("abstract")
                    state.draft_title = node_output.get("draft_title")
                    state.draft_text = node_output.get("draft_text")

                elif node_name == "refine":
                    yield {"type": "log", "message": "🔧 Refinement complete."}
                    # Update state
                    if node_output.get("abstract"):
                        state.abstract = node_output.get("abstract")
                    state.final_text = node_output.get("final_text")

                elif node_name == "pdf":
                    pdf_path = node_output.get("output_pdf")
                    yield {"type": "log", "message": f"📄 PDF generated at {pdf_path}"}
                    
                    # Update state with final results
                    state.output_pdf = pdf_path
                    state.job_id = node_output.get("job_id")
                    state.title = node_output.get("title")
                    state.status = "COMPLETED"
                    state.generation_time_s = round(time.time() - state.start_time, 2)
                    # Ensure abstract is passed if not already updated
                    if node_output.get("abstract"):
                        state.abstract = node_output.get("abstract")

        yield {"type": "log", "message": f"🏁 Research generation complete in {state.generation_time_s} sec."}
        
        # Yield final result
        result_data = {
            "job_id": state.job_id,
            "title": state.title or "Untitled Research Paper",
            "abstract": state.abstract or "No abstract available.",
            "status": state.status or "COMPLETED",
            "pdf_path": state.output_pdf,
            "generation_time": state.generation_time_s,
            "num_sections": len(state.sections),
            "num_references": len(state.references)
        }
        yield {"type": "result", "data": result_data}

    except Exception as e:
        yield {"type": "error", "message": f"💥 Workflow crashed: {str(e)}"}

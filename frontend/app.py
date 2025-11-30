"""
Streamlit frontend for Paperoid Research Paper Generator
Enhanced with real-time progress updates and plagiarism detection.
"""

import streamlit as st
import requests
import time
import base64
import os
import json

# --- Configuration ---
API_URL = "http://127.0.0.1:8000"
GENERATE_ENDPOINT = f"{API_URL}/generate-paper/"
CHECK_PLAGIARISM_ENDPOINT = f"{API_URL}/check-plagiarism/"

st.set_page_config(
    page_title="Paperoid AI", 
    page_icon="📄", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS (Premium Design) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 1.2rem;
        margin-bottom: 3rem;
        font-weight: 400;
    }

    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.8rem;
        border-radius: 12px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
    }

    .progress-log {
        background: #f8f9fa;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        border-left: 3px solid #667eea;
        margin: 0.3rem 0;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.9rem;
    }

    .plag-card {
        padding: 1rem;
        border-radius: 10px;
        background: #fff;
        border-left: 5px solid #667eea;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        color: #333; /* Force dark text for visibility in dark mode */
    }
    
    .plag-card h4 {
        color: #1e293b;
        margin: 0 0 0.5rem 0;
    }
    
    .plag-card p {
        color: #475569;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
    }

    .similarity-high { border-left-color: #dc3545; }
    .similarity-med { border-left-color: #ffc107; }
    .similarity-low { border-left-color: #28a745; }

</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<h1 class="main-header">Paperoid AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Generate structured research papers & check for overlaps</p>', unsafe_allow_html=True)

# --- Sidebar / Status ---
with st.sidebar:
    st.header("System Status")
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=2)
        if health_response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("⚠️ API Not Responding")
    except:
        st.error("❌ API Offline")
        st.warning("Ensure backend is running: `uvicorn main:app --reload`")

# --- Main Input Section ---
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🧠 Research Configuration")
    topic = st.text_input("Research Topic", placeholder="e.g., Generative Adversarial Networks in Medical Imaging")
    keywords = st.text_input("Keywords (optional)", placeholder="GANs, MRI, CT scan, synthetic data")

with col2:
    st.markdown("### ⚙️ Settings")
    domain = st.selectbox("Domain", ["Computer Science", "AI/ML", "Healthcare", "Finance", "Physics", "Other"])
    length = st.slider("Pages", 3, 15, 5)
    num_refs = st.number_input("Min References", 5, 30, 10)

generate_btn = st.button("🚀 Generate Research Paper", type="primary")

# --- Session State for Results ---
if "paper_data" not in st.session_state:
    st.session_state.paper_data = None
if "plag_results" not in st.session_state:
    st.session_state.plag_results = None

# --- Generation Logic ---
if generate_btn:
    if not topic.strip():
        st.warning("⚠️ Please enter a research topic.")
    else:
        # Reset previous results
        st.session_state.paper_data = None
        st.session_state.plag_results = None
        
        st.markdown("### 🔄 Generation Progress")
        
        # Use st.status for cleaner progress UI
        with st.status("🚀 Starting research generation...", expanded=True) as status:
            try:
                start_time = time.time()
                payload = {
                    "topic_or_prompt": topic.strip(),
                    "page_length": length,
                    "num_references": num_refs,
                    "word_count": length * 500
                }
                if keywords.strip():
                    payload["title"] = f"{topic} - {keywords}"

                # Stream the response
                response = requests.post(
                    GENERATE_ENDPOINT, 
                    json=payload, 
                    timeout=300, 
                    stream=True
                )
                
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                update = json.loads(line.decode('utf-8'))
                                
                                if update["type"] == "log":
                                    status.write(f"🔄 {update['message']}")
                                    
                                elif update["type"] == "result":
                                    st.session_state.paper_data = update["data"]
                                    elapsed = round(time.time() - start_time, 2)
                                    status.update(label=f"✅ Generation Complete in {elapsed}s!", state="complete", expanded=False)
                                    
                                elif update["type"] == "error":
                                    status.update(label="❌ Generation Failed", state="error")
                                    st.error(update["message"])
                                    
                            except json.JSONDecodeError:
                                continue
                
                else:
                    status.update(label="❌ API Error", state="error")
                    st.error(f"❌ API Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                status.update(label="⏱️ Timeout", state="error")
                st.error("⏱️ Request timed out. The paper generation is taking longer than expected.")
            except Exception as e:
                status.update(label="⚠️ Error", state="error")
                st.error(f"⚠️ Error: {str(e)}")

# --- Display Generated Paper ---
if st.session_state.paper_data:
    data = st.session_state.paper_data
    st.markdown("---")
    st.markdown("## 📊 Generated Paper")
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["📄 Paper Details", "📥 Download & Preview"])
    
    with tab1:
        st.markdown(f"### {data.get('title', 'Untitled')}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📑 Sections", data.get('num_sections', 0))
        c2.metric("📚 References", data.get('num_references', 0))
        c3.metric("⏱️ Time", f"{data.get('generation_time', 0)}s")
        
        st.markdown("### Abstract")
        st.info(data.get('abstract', 'No abstract available.'))
        
    with tab2:
        pdf_path = data.get("pdf_path")
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            
            col_d1, col_d2 = st.columns([1, 2])
            with col_d1:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=f"research_paper_{data.get('job_id')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                st.caption(f"Job ID: `{data.get('job_id')}`")
            
            with col_d2:
                base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" style="border-radius:12px; border: 1px solid #ddd;"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ PDF file not found. Path: {pdf_path}")

    # --- Plagiarism Check Section (Outside Tabs) ---
    st.markdown("---")
    st.markdown("### 🕵️ Similarity Check (arXiv)")
    st.caption("Check for papers with similar abstracts on arXiv")
    
    if st.button("🔍 Run Similarity Check", key="plag_check_btn"):
        with st.spinner("Searching arXiv..."):
            try:
                search_abstract = data.get('abstract', '')
                if not search_abstract or search_abstract == "No abstract available.":
                    search_abstract = topic
                    
                plag_payload = {
                    "title": data.get('title', topic),
                    "abstract": search_abstract
                }
                plag_resp = requests.post(CHECK_PLAGIARISM_ENDPOINT, json=plag_payload, timeout=30)
                
                if plag_resp.status_code == 200:
                    resp_data = plag_resp.json()
                    st.session_state.plag_results = resp_data.get("similar_papers", [])
                    st.session_state.plag_score = resp_data.get("overall_score", 0.0)
                else:
                    st.error(f"❌ Check failed: {plag_resp.text}")
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")

    # Display plagiarism results
    if st.session_state.plag_results is not None:
        results = st.session_state.plag_results
        overall_score = st.session_state.get("plag_score", 0.0)
        
        # Calculate Average Score for display
        avg_score = 0.0
        if results:
            avg_score = sum(p['similarity_score'] for p in results) / len(results)
        
        # Display Scores
        score_color = "green"
        if overall_score > 50: score_color = "red"
        elif overall_score > 20: score_color = "orange"
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div style="padding: 1rem; background: #f0f2f6; border-radius: 10px; margin-bottom: 1rem; text-align: center;">
                <h3 style="margin:0;">Max Similarity Score</h3>
                <h1 style="color: {score_color}; font-size: 3rem; margin:0;">{overall_score}%</h1>
                <p style="color: #666;">Highest single match found</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div style="padding: 1rem; background: #f0f2f6; border-radius: 10px; margin-bottom: 1rem; text-align: center;">
                <h3 style="margin:0;">Average Similarity</h3>
                <h1 style="color: #333; font-size: 3rem; margin:0;">{round(avg_score, 1)}%</h1>
                <p style="color: #666;">Average across all {len(results)} results</p>
            </div>
            """, unsafe_allow_html=True)

        if not results:
            st.success("✅ No significant similarity found in arXiv papers.")
        else:
            st.info(f"Found {len(results)} relevant papers (sorted by similarity):")
            for paper in results:
                score = paper['similarity_score']
                color_class = "similarity-low"
                if score > 50: 
                    color_class = "similarity-high"
                elif score > 20: 
                    color_class = "similarity-med"
                
                st.markdown(f"""
                <div class="plag-card {color_class}">
                    <h4>{paper['title']}</h4>
                    <p><b>Similarity: {score}%</b></p>
                    <p style="font-size:0.9rem; color:#31333F;">{paper['summary'][:200]}...</p>
                    <a href="{paper.get('pdf') or paper.get('link')}" target="_blank">Read Paper &rarr;</a>
                </div>
                """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #aaa; font-size: 0.9rem;'>Paperoid AI v2.0 • Powered by LangGraph & LLaMA</div>", unsafe_allow_html=True)
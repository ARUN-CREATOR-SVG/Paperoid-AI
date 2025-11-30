"""
Streamlit frontend for Paperoid Research Paper Generator

Run with:
    streamlit run frontend.py
"""

import streamlit as st
import requests
import time
import base64
import os


API_URL = "http://127.0.0.1:8000"
GENERATE_ENDPOINT = f"{API_URL}/generate-paper/"

st.set_page_config(
    page_title="Paperoid AI", 
    page_icon="📄", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.75rem;
        border-radius: 8px;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .info-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📄 Paperoid AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Generate structured research papers using AI</p>', unsafe_allow_html=True)

try:
    health_response = requests.get(f"{API_URL}/health", timeout=2)
    if health_response.status_code == 200:
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.error("⚠️ API Not Responding")
except:
    st.sidebar.error("❌ API Offline")
    st.error("⚠️ Backend API is not running. Please start the FastAPI server with: `uvicorn main:app --reload`")

st.markdown("### 📝 Paper Configuration")

col1, col2 = st.columns(2)

with col1:
    topic = st.text_input(
        "🧠 Research Topic", 
        placeholder="e.g., Machine Learning in Healthcare",
        help="Main topic for your research paper"
    )

with col2:
    length = st.slider(
        "📏 Paper Length (pages)", 
        min_value=3, 
        max_value=15, 
        value=5,
        help="Approximate number of pages"
    )

keywords = st.text_area(
    "🔍 Keywords (optional)", 
    placeholder="machine learning, neural networks, healthcare",
    help="Comma-separated keywords to guide the research"
)

domain = st.selectbox(
    "🌐 Domain",
    ["Computer Science", "AI/ML", "Healthcare", "Finance", "Physics", "Biology", "Other"],
    help="Select the research domain"
)

num_refs = st.number_input(
    "📚 Minimum References",
    min_value=5,
    max_value=20,
    value=10,
    help="Minimum number of references to include"
)

st.markdown("---")


generate_btn = st.button("🚀 Generate Research Paper", type="primary")

if generate_btn:
    if not topic.strip():
        st.warning("⚠️ Please enter a research topic to generate the paper.")
    else:
        with st.spinner("🧩 Generating your research paper... This may take 1-3 minutes ⏳"):
            try:
                start_time = time.time()
                
                payload = {
                    "topic_or_prompt": topic.strip(),
                    "page_length": length,
                    "num_references": num_refs,
                    "word_count": length * 500  
                }
                
                if keywords.strip():
                    payload["title"] = f"{topic} - {keywords[:50]}"

                response = requests.post(GENERATE_ENDPOINT, json=payload, timeout=300)
                end_time = time.time()

                if response.status_code == 200:
                    data = response.json()
                    
                    st.success("✅ Paper generated successfully!")
                    
                    st.markdown("### 📊 Generation Summary")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Job ID", data.get('job_id', 'N/A'))
                    with col2:
                        st.metric("Status", data.get('status', 'Unknown'))
                    with col3:
                        st.metric("Time (sec)", f"{data.get('generation_time', 0):.1f}")
                    
                    st.markdown("---")
                    
                    st.markdown("### 📘 Paper Details")
                    st.markdown(f"**Title:** {data.get('title', 'Untitled')}")
                    
                    with st.expander("📄 Abstract", expanded=True):
                        st.write(data.get('abstract', 'No abstract available.'))
                    
                    st.info(f"📑 **Sections:** {data.get('num_sections', 0)} | 📚 **References:** {data.get('num_references', 0)}")
                    
                    st.markdown("---")
                    
                    # ✅ PDF Display and Download
                    st.markdown("### 📥 Download & Preview")
                    
                    pdf_path = data.get("pdf_path")

                    if pdf_path and os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()

                        # ✅ Download button (prominent)
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=f"research_paper_{data.get('job_id', 'output')}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                        
                        st.markdown("---")
                        
                        # ✅ PDF Preview
                        with st.expander("👁️ Preview PDF", expanded=False):
                            base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                            pdf_display = f"""
                            <iframe src="data:application/pdf;base64,{base64_pdf}"
                                    width="100%" height="800" type="application/pdf"
                                    style="border: 1px solid #ddd; border-radius: 8px;">
                            </iframe>
                            """
                            st.markdown(pdf_display, unsafe_allow_html=True)
                    else:
                        st.error(f"⚠️ PDF not found at: {pdf_path}")
                        st.info("The PDF may have been generated but the path is incorrect. Check the `output/` directory.")
                
                elif response.status_code == 500:
                    st.error(f"❌ Server Error: {response.json().get('detail', 'Unknown error')}")
                else:
                    st.error(f"❌ Error: {response.status_code} - {response.text}")

            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. The paper generation is taking longer than expected.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection Error: Cannot reach the API. Make sure the backend is running.")
            except Exception as e:
                st.error(f"⚠️ Unexpected Error: {str(e)}")
                st.info("Check the console logs for more details.")

# ✅ Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>Built with ❤️ using FastAPI, LangGraph, and Streamlit</p>
    <p style="font-size: 0.9rem;">Powered by Meta LLaMA 3</p>
</div>
""", unsafe_allow_html=True)


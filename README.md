# Paperoid AI - Automated Research Paper Generator 📄🤖

**Paperoid AI** is a novel software solution designed to automate the lifecycle of research paper generation. Leveraging the cutting-edge capabilities of **Generative AI** and **Large Language Models (LLMs)**, specifically **Meta's LLaMA 3**, Paperoid AI introduces an autonomous "Agentic" workflow.

Unlike traditional text generators that produce unstructured text, Paperoid AI utilizes **LangGraph** to orchestrate a team of specialized AI agents—a Retriever, a Writer, and a Refiner—that collaborate to produce a high-quality research document.

---

## 🚀 Features

-   **Agentic Workflow**: Mimics the human research process (Search -> Draft -> Refine) using LangGraph.
-   **Retrieval-Augmented Generation (RAG)**: Queries the **arXiv** database to fetch real-time, authoritative research papers.
-   **Structured Output**: Generates a structured draft including Abstract, Introduction, Related Work, Methodology, Results, and Conclusion.
-   **Plagiarism/Similarity Check**: Verifies the originality of the generated abstract against existing works using sequence matching.
-   **PDF Export**: Compiles the final text into a formatted PDF document ready for review.
-   **Real-time Feedback**: Streams logs to the user interface during the generation process.

## 🛠️ Tech Stack

-   **Frontend**: [Streamlit](https://streamlit.io/)
-   **Backend**: [FastAPI](https://fastapi.tiangolo.com/)
-   **AI/LLM Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph), [LangChain](https://www.langchain.com/)
-   **LLM Provider**: [HuggingFace Inference API](https://huggingface.co/inference-api) (Meta LLaMA 3)
-   **Data Source**: [arXiv API](https://arxiv.org/help/api)
-   **PDF Generation**: [FPDF2](https://pyfpdf.github.io/fpdf2/)

## 📂 Project Structure

```
Paperoid-AI/
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── backend/
│   ├── __init__.py
│   ├── main.py             # FastAPI Server
│   ├── schemas/            # Pydantic Models
│   ├── agents/             # AI Agents (Retriever, Writer, Refiner)
│   ├── tools/              # Utility Scripts (arXiv, PDF)
│   └── workflow/           # LangGraph Logic
├── frontend/
│   ├── app.py              # Streamlit App
│   └── assets/             # Static files
└── output/                 # Generated PDFs
```

## ⚙️ Installation & Setup

### Prerequisites

-   Python 3.10 or higher
-   Git

### Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-repo/paperoid-ai.git
    cd Paperoid-AI
    ```

2.  **Create a Virtual Environment**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Linux/macOS
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r backend/requirements.txt
    pip install -r frontend/requirements.txt
    ```
    *(Note: Ensure you install dependencies for both backend and frontend if they are separate, or use the root requirements if provided.)*

4.  **Environment Configuration**
    Create a `.env` file in the root directory and add your HuggingFace API Token:
    ```env
    HUGGINGFACEHUB_API_TOKEN=your_hf_token_here
    ```

## 🏃‍♂️ Usage

To run the application, you need to start both the backend server and the frontend interface.

### 1. Start the Backend (FastAPI)
Open a terminal and run:
```bash
uvicorn backend.main:app --reload
```
The backend will start at `http://localhost:8000`.

### 2. Start the Frontend (Streamlit)
Open a new terminal (keep the backend running) and run:
```bash
streamlit run frontend/app.py
```
The application will open in your browser at `http://localhost:8501`.

## 📝 How to Use

1.  **Enter Topic**: Input your research topic (e.g., "Generative Adversarial Networks") in the main text field.
2.  **Configure**: Adjust the number of pages and references using the sidebar or settings.
3.  **Generate**: Click the **"🚀 Generate Research Paper"** button.
4.  **Monitor**: Watch the real-time logs as the agents search, write, and refine the content.
5.  **Download**: Once complete, download the generated PDF.
6.  **Check Plagiarism**: Go to the "Plagiarism Check" tab to verify the originality of the abstract.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

[MIT License](LICENSE)

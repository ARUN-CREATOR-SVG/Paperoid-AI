from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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

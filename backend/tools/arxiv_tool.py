import requests
import xml.etree.ElementTree as ET
from langchain_core.tools import tool

def parse_arxiv_xml(xml_content: str, topic: str = "") -> list[dict]:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_content)
    papers = []
    
    topic_keywords = topic.lower().split()

    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns).text.strip()
        summary = entry.find("atom:summary", ns).text.strip()
        link = entry.find("atom:id", ns).text.strip()
        
        # Strict Relevance Check: At least one keyword must be in title or summary
        # For multi-word topics like "Subaru from ReZero", we check if significant parts exist
        text_to_check = (title + " " + summary).lower()
        
        # If topic is provided, check for relevance
        if topic:
             # Check if at least 50% of keywords are present
             matches = sum(1 for word in topic_keywords if word in text_to_check)
             if matches / len(topic_keywords) < 0.5:
                 continue

        pdf_link = None
        for l in entry.findall("atom:link", ns):
            if l.attrib.get("type") == "application/pdf":
                pdf_link = l.attrib.get("href")
        papers.append({
            "title": title,
            "summary": summary,
            "link": link,
            "pdf": pdf_link
        })
    return papers

@tool
def arxiv_search(topic: str, max_results: int = 5) -> list[dict]:
    """Search arXiv for recent papers on a topic"""
    return search_arxiv(topic, max_results)

def search_arxiv(topic: str, max_results: int = 5) -> list[dict]:
    """Direct function to search arXiv (not a tool)."""
    url = f"http://export.arxiv.org/api/query?search_query=all:{topic}&max_results={max_results}"
    resp = requests.get(url)
    if not resp.ok:
        raise ValueError("Failed to fetch from arXiv.")
    return parse_arxiv_xml(resp.text, topic=topic)

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity using Jaccard Similarity (Word Overlap).
    This is better for detecting content overlap than simple sequence matching.
    """
    # Normalize text: lowercase and remove common punctuation
    t1 = text1.lower().replace(".", "").replace(",", "").replace("!", "").split()
    t2 = text2.lower().replace(".", "").replace(",", "").replace("!", "").split()
    
    # Create sets of unique words (shingles)
    s1 = set(t1)
    s2 = set(t2)
    
    # Calculate Jaccard Index: Intersection / Union
    intersection = len(s1.intersection(s2))
    union = len(s1.union(s2))
    
    if union == 0:
        return 0.0
        
    return intersection / union

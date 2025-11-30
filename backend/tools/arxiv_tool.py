import requests
import xml.etree.ElementTree as ET
from langchain_core.tools import tool

def parse_arxiv_xml(xml_content: str) -> list[dict]:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_content)
    papers = []

    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns).text.strip()
        summary = entry.find("atom:summary", ns).text.strip()
        link = entry.find("atom:id", ns).text.strip()
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
    url = f"http://export.arxiv.org/api/query?search_query=all:{topic}&max_results={max_results}"
    resp = requests.get(url)
    if not resp.ok:
        raise ValueError("Failed to fetch from arXiv.")
    return parse_arxiv_xml(resp.text)

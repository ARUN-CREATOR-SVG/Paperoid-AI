import requests
import json

API_URL = "http://127.0.0.1:8000"

def test_plagiarism_check():
    print("Testing Plagiarism Check Endpoint...")
    
    # Use a known paper title and abstract (e.g., Attention Is All You Need)
    payload = {
        "title": "Attention Is All You Need",
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely."
    }
    
    try:
        response = requests.post(f"{API_URL}/check-plagiarism/", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(json.dumps(data, indent=2))
            
            papers = data.get("similar_papers", [])
            if papers:
                print(f"Found {len(papers)} similar papers.")
                print(f"Top match: {papers[0]['title']} (Score: {papers[0]['similarity_score']}%)")
            else:
                print("⚠️ No similar papers found (unexpected for this title).")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_plagiarism_check()

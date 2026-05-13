import requests
import json

def test_live_api():
    url = "http://localhost:8000/process-voice"
    file_path = "uploads/1fa3e2e7-e3a0-4429-bcd7-af580bb91e39.webm"
    
    print(f"Testing live API at {url} with file {file_path}...")
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": ("recording.webm", f, "audio/webm")}
            response = requests.post(url, files=files)
            
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("\nResponse Body:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("\nError Response:")
            print(response.text)
            
    except Exception as e:
        print(f"Error during request: {e}")

if __name__ == "__main__":
    test_live_api()

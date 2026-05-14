import requests
import os
import json

def test_process_voice():
    url = "http://127.0.0.1:8000/process-voice"
    
    # Use an existing file from uploads for testing
    upload_dir = "uploads"
    files = [f for f in os.listdir(upload_dir) if f.endswith(".webm")]
    if not files:
        print("No .webm files found in uploads for testing.")
        return
        
    test_file = os.path.join(upload_dir, files[0])
    print(f"Testing with file: {test_file}")
    
    with open(test_file, "rb") as f:
        files = {"file": (os.path.basename(test_file), f, "audio/webm")}
        # Optional: mock frontend features
        data = {
            "audio_analysis": json.dumps({
                "pitch_mean": 70.0,
                "jitter": 0.09,
                "loudness": 0.1,
                "voice_description": "trembling, quiet voice detected by browser"
            })
        }
        
        print("Sending request to /process-voice...")
        response = requests.post(url, files=files, data=data)
        
    print(f"Status Code: {response.status_code}")
    result = response.json()
    if response.status_code == 200 and "error" not in result:
        print("\nSuccess! Result:")
        print(f"Transcript: {result.get('transcript')}")
        print(f"Emotion: {result.get('emotion', {}).get('emotion')}")
        print(f"AI Response: {result.get('response')}")
        print(f"Audio URL: {result.get('audio_url')}")
    else:
        print("\nPipeline Error:")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_process_voice()

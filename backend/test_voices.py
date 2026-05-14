import requests

BASE_URL = "http://localhost:8000"

def test_preview(voice_name):
    print(f"Testing preview for {voice_name}...")
    response = requests.post(f"{BASE_URL}/preview-voice", data={"voice_name": voice_name})
    if response.status_code == 200:
        print(f"SUCCESS: {response.json()}")
    else:
        print(f"FAILED: {response.status_code} - {response.text}")

def test_process_voice(voice_name):
    print(f"Testing process-voice for {voice_name}...")
    # Using a dummy file for testing (this might fail if the file is invalid for Whisper)
    # But we can at least check if the parameter is accepted
    files = {'file': ('test.webm', b'fake audio data', 'audio/webm')}
    data = {'voice_name': voice_name}
    response = requests.post(f"{BASE_URL}/process-voice", files=files, data=data)
    # We expect a failure on transcription but let's see if it crashes before that
    print(f"Response: {response.status_code}")

if __name__ == "__main__":
    test_preview("Josh")
    test_preview("Amelia")

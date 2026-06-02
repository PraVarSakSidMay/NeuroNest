import os
import sys
import json
import requests

BACKEND_URL = "http://localhost:8000"

def test_session_start():
    print("\n--- Testing /session-start ---")
    url = f"{BACKEND_URL}/session-start"
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
        assert "greeting" in response.json()
        print("[OK] /session-start passed!")
    except Exception as e:
        print(f"[FAIL] /session-start failed: {e}")
        return False
    return True

def test_preview_voice():
    print("\n--- Testing /preview-voice ---")
    url = f"{BACKEND_URL}/preview-voice"
    data = {"voice_name": "Rachel"}
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
        res_data = response.json()
        assert "audio_url" in res_data or "error" in res_data
        print("[OK] /preview-voice passed!")
    except Exception as e:
        print(f"[FAIL] /preview-voice failed: {e}")
        return False
    return True

def test_process_voice():
    print("\n--- Testing /process-voice ---")
    url = f"{BACKEND_URL}/process-voice"
    audio_path = os.path.join(os.path.dirname(__file__), "test_deepgram.mp3")
    if not os.path.exists(audio_path):
        # try parent directory
        audio_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_deepgram.mp3")
    
    if not os.path.exists(audio_path):
        print(f"❌ Test audio file not found at {audio_path}")
        return False
        
    print(f"Using audio file: {audio_path}")
    
    files = {"file": ("test_deepgram.mp3", open(audio_path, "rb"), "audio/mp3")}
    data = {
        "voice_name": "Rachel",
        "audio_analysis": json.dumps({
            "pitch_mean": 150.0,
            "jitter": 0.02,
            "loudness": 0.05,
            "volume_std_dev": 12.0,
            "pitch_std_dev": 18.0,
            "is_trembling": False,
            "is_singing": False,
            "is_crying": False,
            "is_whispering": False,
            "voice_description": "Normal voice"
        })
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status Code: {response.status_code}")
        res_json = response.json()
        # Clean up output for presentation
        if "response" in res_json:
            print(f"AI Response: {res_json['response']}")
        if "transcript" in res_json:
            print(f"Transcript: {res_json['transcript']}")
        if "emotion" in res_json:
            print(f"Emotion: {res_json['emotion']}")
        if "dashboard" in res_json:
            print(f"Dashboard Update: {res_json['dashboard']}")
        
        assert response.status_code == 200
        assert "transcript" in res_json
        assert "emotion" in res_json
        assert "response" in res_json
        assert "dashboard" in res_json
        print("[OK] /process-voice passed!")
    except Exception as e:
        print(f"[FAIL] /process-voice failed: {e}")
        return False
    finally:
        files["file"][1].close()
    return True

if __name__ == "__main__":
    success = True
    success &= test_session_start()
    success &= test_preview_voice()
    success &= test_process_voice()
    if not success:
        sys.exit(1)
    else:
        print("\n[OK] All endpoints verified successfully!")

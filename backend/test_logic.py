from services.emotion_service import analyze_emotion
from services.response_service import generate_response
import json

def run_test():
    print("--- Running Contradiction Test ---")
    
    # 1. Mock the transcript (saying they are fine)
    transcript = "You know what, I am fine. There is nothing wrong."
    print(f"\n[Transcript]: {transcript}")

    # 2. Mock audio features from openSMILE indicating high distress
    # We pass it as a dict since that's what opensmile_service returns
    audio_features = {
        "pitch_mean": 65.2, # high pitch
        "jitter": 0.08,     # very high jitter (trembling voice)
        "loudness": 0.2,    # quiet, withdrawn
        "human_readable_description_for_test": "Voice sounds like it is whimpering, sniffing, shivering, and trying to hold back crying."
    }
    print(f"\n[Audio Features (Mocked)]: {json.dumps(audio_features, indent=2)}")

    print("\n--- Running Emotion Service ---")
    # 3. Get emotion data
    emotion_data = analyze_emotion(transcript, audio_features)
    print(f"\n[Detected Emotion Data]:")
    print(json.dumps(emotion_data, indent=2))

    print("\n--- Running Response Service ---")
    # 4. Generate response
    ai_response = generate_response(transcript, emotion_data)
    print(f"\n[AI Response]:")
    print(ai_response)

if __name__ == "__main__":
    run_test()

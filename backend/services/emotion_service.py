import json
from .model_manager import model_manager

def analyze_emotion(transcript, audio_features):

    prompt = f"""
    Analyze the emotional state by comparing the literal meaning of the transcript with the provided audio features. 
    Pay close attention to contradictions (e.g., if the user says "I am fine" but the audio features indicate high stress, crying, shivering, or nervousness).

    Transcript:
    {transcript}

    Audio Features:
    {audio_features}

    Return JSON strictly in this format:
    {{
      "emotion": "string (the overarching emotion detected)",
      "stress_level": 0-100 (integer representing stress level),
      "tone": "string (e.g., trembling, calm, aggressive)",
      "contradiction_detected": boolean (true if words contradict the voice tone),
      "hidden_emotion": "string (if contradiction_detected is true, what is the underlying emotion? e.g. 'hiding sadness', 'suppressing fear'. otherwise empty string)"
    }}
    """

    content = model_manager.get_llm_response(transcript, prompt, json_mode=True)
    
    try:
        # Clean up code blocks if model returns them
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"Error parsing emotion JSON: {e}. Raw content: {content}")
        return {
            "emotion": "neutral",
            "stress_level": 50,
            "tone": "unknown",
            "contradiction_detected": False,
            "hidden_emotion": ""
        }


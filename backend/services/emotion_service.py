from groq import Groq, RateLimitError
import json
from dotenv import load_dotenv

load_dotenv()
client = Groq()

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

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content

        return json.loads(content)
    except RateLimitError:
        print("WARNING: Groq Quota Exceeded. Using mock emotion analysis fallback for Hackathon.")
        return {
            "emotion": "distressed",
            "stress_level": 85,
            "tone": "trembling",
            "contradiction_detected": True,
            "hidden_emotion": "hiding sadness or fear"
        }


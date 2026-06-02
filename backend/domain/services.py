"""Domain services for emotion analysis."""
from typing import Protocol, Optional
from .value_objects import Emotion, AudioFeatures, Transcript


class IEmotionAnalyzer(Protocol):
    """Protocol for emotion analysis services."""
    
    def analyze(
        self,
        transcript: Transcript,
        audio_features: Optional[AudioFeatures] = None,
    ) -> Emotion:
        """Analyze emotion from transcript and optional audio features."""
        ...


class EmotionAnalyzerService:
    """Concrete emotion analyzer service."""
    
    def __init__(self, model_manager=None):
        self.model_manager = model_manager
    
    def analyze(
        self,
        transcript: Transcript,
        audio_features: Optional[AudioFeatures] = None,
    ) -> Emotion:
        """Analyze emotion from transcript and optional audio features."""
        import json
        from services.model_manager import model_manager
        
        prompt = f"""
        Analyze the emotional state by comparing the literal meaning of the transcript with the provided audio features. 
        Pay close attention to contradictions (e.g., if the user says "I am fine" but the audio features indicate high stress, crying, shivering, or nervousness).

        Transcript:
        {transcript.text}

        Audio Features:
        {audio_features.model_dump() if audio_features else "None"}

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
            content = model_manager.get_llm_response(transcript.text, prompt, json_mode=True)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            return Emotion(
                emotion=data.get("emotion", "neutral"),
                stress_level=data.get("stress_level", 50),
                tone=data.get("tone", "calm"),
                contradiction_detected=data.get("contradiction_detected", False),
                hidden_emotion=data.get("hidden_emotion", ""),
                confidence=0.85,
            )
        except Exception:
            return Emotion(
                emotion="neutral",
                stress_level=50,
                tone="unknown",
                contradiction_detected=False,
                hidden_emotion="",
                confidence=0.5,
            )
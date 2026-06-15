import json
from .model_manager import model_manager
from core.logger import logger

class EmotionAnalyzer:
    """Base class for modality-specific emotion analyzers."""
    def analyze(self, data) -> dict:
        raise NotImplementedError

class TranscriptAnalyzer(EmotionAnalyzer):
    def analyze(self, transcript: str) -> dict:
        return {"transcript": transcript}

class AudioAnalyzer(EmotionAnalyzer):
    def analyze(self, audio_features: dict) -> dict:
        hint = audio_features.get("audio_emotion_hint", "") if isinstance(audio_features, dict) else ""
        return {"features": audio_features, "hint": hint}

class VideoAnalyzer(EmotionAnalyzer):
    def analyze(self, video_features: dict) -> dict:
        if not video_features:
            return {}
        info = f"\nVideo Facial Features:\n{json.dumps(video_features, indent=2)}\n"
        if video_features.get("timeline"):
            info += (
                "\nThe video features summarize the full recording window, not a single frame. "
                "Prioritize emotion_distribution, sample_count, eye_contact_ratio, head_pose, "
                "masking flags, and the timeline when deciding the user's actual emotional state.\n"
            )
        return {"features": video_features, "info": info}

class EmotionService:
    """
    Service for multimodal emotion fusion following OCP (Open/Closed) and SRP (Single Responsibility).
    It coordinates various modality-specific analyzers to form a comprehensive emotional profile.
    """
    
    def __init__(self, model_manager):
        # Facade to LLM services for final fusion reasoning
        self.model_manager = model_manager
        # Modality-specific analyzer strategies
        self.transcript_analyzer = TranscriptAnalyzer()
        self.audio_analyzer = AudioAnalyzer()
        self.video_analyzer = VideoAnalyzer()

    def analyze_emotion(self, transcript, audio_features, video_features=None):
        """
        Main entry point for emotion fusion.
        1. Analyzes each modality independently.
        2. Builds a comprehensive reasoning prompt for the LLM.
        3. Parses and enriches the final results with raw telemetry.
        """
        # Independent modality analysis
        t_data = self.transcript_analyzer.analyze(transcript)
        a_data = self.audio_analyzer.analyze(audio_features)
        v_data = self.video_analyzer.analyze(video_features)

        logger.info(
            "Emotion fusion processing started",
            transcript_preview=transcript[:120],
            video_present=bool(video_features),
        )

        # Build the multimodal reasoning prompt
        prompt = self._build_prompt(t_data, a_data, v_data)
        
        # Use LLM to perform high-level cross-modal reasoning
        content = self.model_manager.get_llm_response(transcript, prompt, json_mode=True)
        
        # Parse the JSON response from the LLM
        result = self._parse_result(content)
        
        # Enrich the parsed result with raw telemetry (eye contact, head pose, etc.)
        return self._enrich_result(result, audio_features, video_features)

    def _build_prompt(self, t_data, a_data, v_data):
        return f"""
        Analyze the emotional state of the user with high precision by cross-referencing three modalities:
        1. TRANSCRIPT: Literal meaning and linguistic cues.
        2. AUDIO FEATURES: Vocal characteristics (pitch, jitter, volume, crying/whispering markers).
        3. VIDEO FEATURES: Detailed facial Action Units, micro-expressions, smile/frown intensity, and gaze behavior.

        CRITICAL INSTRUCTIONS:
        - VIDEO PRIORITY: Facial Action Units (AU) are the most reliable indicators of true emotion. Even if the user sounds calm or says they are fine, if AU12 (lip corner puller) is absent but AU15 (lip corner depressor) or AU4 (brow lowerer) are present, prioritize the facial markers.
        - MASKING DETECTION: Look for "fake smiles" (AU12 without AU6 eye crinkling) or forced calmness that contradicts facial tension.
        - TIMELINE ANALYSIS: If a timeline is provided, look for emotional shifts during the recording.
        - BE OBJECTIVE: Do not default to 'sad' or 'neutral'. If the cues indicate 'excited', 'confused', or 'frustrated', label them as such.

        Transcript:
        {t_data['transcript']}

        Audio Features:
        {a_data['features']}

        Audio Emotion Hint: {a_data['hint']}
        {v_data.get('info', '')}

        Return JSON strictly in this format:
        {{
          "emotion": "string (the overarching fused emotion detected. MUST be one of: 'neutral', 'happy', 'sad', 'angry', 'anxious', 'fearful', 'surprised', 'disgusted', 'confused', 'excited', 'frustrated', 'depressed', 'calm')",
          "stress_level": 0-100 (integer representing stress level),
          "tone": "string (e.g., trembling, calm, aggressive)",
          "contradiction_detected": boolean (true if words or voice contradict the facial micro-expressions),
          "hidden_emotion": "string (if contradiction_detected is true, what is the underlying emotion? e.g. 'hiding sadness', 'suppressing fear'. otherwise empty string)"
        }}
        """

    def _parse_result(self, content):
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            required_keys = {"emotion", "stress_level", "tone", "contradiction_detected", "hidden_emotion"}
            if not isinstance(result, dict) or not required_keys.issubset(result.keys()):
                return self._get_default_result(result if isinstance(result, dict) else {})
            return result
        except Exception as e:
            print(f"Error parsing emotion JSON: {e}. Raw content: {content}")
            return self._get_default_result()

    def _get_default_result(self, partial=None):
        partial = partial or {}
        return {
            "emotion": partial.get("emotion", "neutral"),
            "stress_level": partial.get("stress_level", 50),
            "tone": partial.get("tone", "unknown"),
            "contradiction_detected": partial.get("contradiction_detected", False),
            "hidden_emotion": partial.get("hidden_emotion", ""),
        }

    def _enrich_result(self, result, audio_features, video_features):
        if video_features:
            result["eye_contact_ratio"] = video_features.get("eye_contact_ratio", 1.0)
            result["head_pose"] = video_features.get("head_pose", {"pitch": 0, "yaw": 0, "roll": 0})
            aus = video_features.get("actionUnits", {})
            if aus:
                result["notable_facial_markers"] = {k: v for k, v in aus.items() if v > 0.4}
        else:
            result["eye_contact_ratio"] = 1.0
            result["head_pose"] = {"pitch": 0, "yaw": 0, "roll": 0}

        if isinstance(audio_features, dict):
            result["vocal_markers"] = {
                "pitch_variation": "high" if audio_features.get("pitch_std", 0) > 20 else "normal",
                "shaking": audio_features.get("is_trembling", False),
                "whispering": audio_features.get("is_whispering", False)
            }
        return result

# Legacy functional wrapper
def analyze_emotion(transcript, audio_features, video_features=None):
    service = EmotionService(model_manager)
    return service.analyze_emotion(transcript, audio_features, video_features)

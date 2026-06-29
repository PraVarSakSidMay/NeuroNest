import json
from typing import Optional
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
    def analyze(self, audio_features: Optional[dict]) -> dict:
        if not isinstance(audio_features, dict):
            return {"features": {}, "hint": ""}
        hint = audio_features.get("audio_emotion_hint", "")
        return {"features": audio_features, "hint": hint}

class VideoAnalyzer(EmotionAnalyzer):
    def analyze(self, video_features: Optional[dict]) -> dict:
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
        Determines the emotion, stress level, tone, and contradiction
        safely and programmatically without LLM calls.
        """
        # Independent modality analysis
        t_data = self.transcript_analyzer.analyze(transcript)
        a_data = self.audio_analyzer.analyze(audio_features)
        v_data = self.video_analyzer.analyze(video_features)

        logger.info(
            "Emotion fusion processing programmatically",
            transcript_preview=transcript[:120],
            video_present=bool(video_features),
        )

        # Baseline values
        fused_emotion = "neutral"
        stress_level = 50
        tone = "calm"
        contradiction_detected = False
        hidden_emotion = ""

        # Parse text/transcript clues (lexical analyzer)
        text_lower = transcript.lower()
        has_positive_words = any(w in text_lower for w in ["great", "happy", "awesome", "good", "excited", "glad", "wonderful", "cool", "nice", "fun", "joy", "delighted", "cheerful", "pleased", "fantastic", "relaxed", "calm", "optimistic", "hopeful", "laugh", "smiling"])
        has_negative_words = any(w in text_lower for w in ["sad", "terrible", "bad", "unhappy", "depressed", "down", "cry", "hate", "hurt", "pain", "grief", "lonely", "hopeless", "miserable", "worthless", "empty", "tired", "exhausted", "heavy", "broken", "weeping", "sobbing", "dark"])
        has_anxious_words = any(w in text_lower for w in ["worry", "anxious", "scared", "fear", "nervous", "panic", "stressed", "stress", "afraid", "terrified", "overwhelmed", "jittery", "shaking", "tightness", "breathless", "dread", "uneasy", "tense"])
        has_angry_words = any(w in text_lower for w in ["angry", "mad", "pissed", "furious", "hate", "annoyed", "frustrated", "irritated", "fuming", "outraged", "resentful", "bitter", "hostile", "screaming", "shouting"])

        # Parse audio clues
        is_trembling = False
        is_whispering = False
        audio_hint = ""
        pitch_std = 0.0

        if isinstance(audio_features, dict):
            trembling_val = audio_features.get("is_trembling", False)
            is_trembling = trembling_val if trembling_val is not None else False
            
            whispering_val = audio_features.get("is_whispering", False)
            is_whispering = whispering_val if whispering_val is not None else False
            
            hint_val = audio_features.get("audio_emotion_hint", "")
            audio_hint = (hint_val or "").lower()
            
            pitch_val = audio_features.get("pitch_std_dev", audio_features.get("pitch_std", 0.0))
            pitch_std = pitch_val if pitch_val is not None else 0.0
            
            jitter_val = audio_features.get("jitter", 0.0)
            jitter = jitter_val if jitter_val is not None else 0.0
            
            vol_val = audio_features.get("volume_std_dev", audio_features.get("vol_std", 0.0))
            vol_std = vol_val if vol_val is not None else 0.0
            
            # Compute physiological stress increment
            stress_level = 50
            if jitter > 0.05:
                stress_level += 15
            if vol_std > 15.0:
                stress_level += 10
            if pitch_std > 25.0:
                stress_level += 10
            if is_trembling:
                stress_level += 15
                tone = "trembling"
            if is_whispering:
                tone = "whispering"
            
            stress_level = min(100, max(0, stress_level))

        # Parse video facial action units (aus)
        eye_contact_ratio = 1.0
        head_pitch = 0.0
        au6 = 0.0
        au12 = 0.0
        au4 = 0.0
        au9 = 0.0   # Nose wrinkle — primary disgust marker
        au10 = 0.0  # Upper lip raise — secondary disgust marker
        au15 = 0.0
        au1 = 0.0
        au2 = 0.0

        if isinstance(video_features, dict):
            eye_contact_ratio = video_features.get("eye_contact_ratio", 1.0)
            head_pose = video_features.get("head_pose", {})
            head_pitch = head_pose.get("pitch", 0.0) if isinstance(head_pose, dict) else 0.0
            aus = video_features.get("actionUnits", {})
            if not aus:
                aus = video_features.get("action_units", {})
            if aus:
                au1 = aus.get("AU01", aus.get("au1", aus.get("AU1", 0.0)))
                au2 = aus.get("AU02", aus.get("au2", aus.get("AU2", 0.0)))
                au4 = aus.get("AU04", aus.get("au4", aus.get("AU4", 0.0)))
                au6 = aus.get("AU06", aus.get("au6", aus.get("AU6", 0.0)))
                au9 = aus.get("AU09", aus.get("au9", aus.get("AU9", 0.0)))
                au10 = aus.get("AU10", aus.get("au10", aus.get("AU10", 0.0)))
                au12 = aus.get("AU12", aus.get("au12", aus.get("AU12", 0.0)))
                au15 = aus.get("AU15", aus.get("au15", aus.get("AU15", 0.0)))

        # Rule-based fusion logic
        # 1. Start with Video FACS (priority)
        if isinstance(video_features, dict) and video_features:
            # Disgust detection (must precede sad — they share AU4/AU15)
            # AU9 (nose wrinkle) is the definitive disgust marker, not present in sadness
            if au9 > 0.35 or (au9 > 0.20 and au10 > 0.20):
                fused_emotion = "disgusted"
                stress_level = max(stress_level, 60) if stress_level > 50 else 60
                tone = "tense"
            # Smile detected
            elif au12 > 0.4:
                # Genuine smile (Duchenne) has cheek raiser (AU6)
                if au6 > 0.4:
                    fused_emotion = "happy"
                    stress_level = max(stress_level, 20) if stress_level > 50 else 20
                    tone = "excited" if au12 > 0.7 else "calm"
                else:
                    # Fake smile: lip corner puller without cheek raiser
                    fused_emotion = "neutral"
                    stress_level = max(stress_level, 60) if stress_level > 50 else 60
                    # Check text context to see if they say they are fine but look tense
                    if has_negative_words or has_anxious_words:
                        contradiction_detected = True
                        hidden_emotion = "sad" if has_negative_words else "anxious"
                        fused_emotion = "confused"
            # Brow furrowed (AU4) - anger, concentration, frustration, or sadness
            elif au4 > 0.4:
                # AU15 (lip depressor) + AU1 (inner brow raise) → sadness
                # But only if AU9 (nose wrinkle) is absent; otherwise it's disgust
                if (au15 > 0.4 or au1 > 0.4) and au9 < 0.25:
                    fused_emotion = "sad"
                    stress_level = max(stress_level, 65) if stress_level > 50 else 65
                    tone = "subdued"
                else:
                    # anger or frustration
                    fused_emotion = "frustrated" if au10 > 0.3 else "angry"
                    stress_level = max(stress_level, 70) if stress_level > 50 else 70
                    tone = "tense"
            # Inner brow raise (AU1) + Outer brow raise (AU2) without AU12 - anxious or surprised
            elif au1 > 0.4:
                if au2 > 0.4:
                    fused_emotion = "surprised" if eye_contact_ratio > 0.8 else "fearful"
                    stress_level = max(stress_level, 60) if stress_level > 50 else 60
                elif au15 > 0.4 and au9 < 0.25:
                    # AU1 (inner brow raise) + AU15 (lip depressor) = grief/sadness (Ekman AU1+15)
                    # Only when AU9 (nose wrinkle) is absent — otherwise still disgust territory
                    fused_emotion = "sad"
                    stress_level = max(stress_level, 65) if stress_level > 50 else 65
                    tone = "subdued"
                else:
                    fused_emotion = "anxious"
                    stress_level = max(stress_level, 70) if stress_level > 50 else 70
                    tone = "nervous"
            # Lip corner depressor (AU15) - sadness ONLY if nose wrinkle is absent
            elif au15 > 0.4 and au9 < 0.25:
                fused_emotion = "sad"
                stress_level = max(stress_level, 60) if stress_level > 50 else 60
                tone = "subdued"

        # 2. Integrate Audio features if video is neutral or absent
        if fused_emotion == "neutral":
            if is_trembling or audio_hint in ["nervous", "anxious", "fearful"]:
                fused_emotion = "anxious"
                stress_level = max(stress_level, 75) if stress_level > 50 else 75
                tone = "trembling"
            elif audio_hint in ["angry", "frustrated"]:
                fused_emotion = "frustrated"
                stress_level = max(stress_level, 70) if stress_level > 50 else 70
                tone = "aggressive" if audio_hint == "angry" else "tense"
            elif audio_hint in ["happy", "excited"]:
                fused_emotion = "happy"
                stress_level = max(stress_level, 30) if stress_level > 50 else 30
                tone = "excited"
            elif audio_hint in ["sad", "depressed"]:
                fused_emotion = "sad"
                stress_level = max(stress_level, 55) if stress_level > 50 else 55
                tone = "subdued"

        # 3. Integrate Text/Sentiment clues to resolve neutral
        if fused_emotion == "neutral":
            if has_positive_words:
                fused_emotion = "happy"
                stress_level = max(stress_level, 30) if stress_level > 50 else 30
                tone = "calm"
            elif has_angry_words:
                fused_emotion = "frustrated"
                stress_level = max(stress_level, 65) if stress_level > 50 else 65
                tone = "tense"
            elif has_anxious_words:
                fused_emotion = "anxious"
                stress_level = max(stress_level, 70) if stress_level > 50 else 70
                tone = "nervous"
            elif has_negative_words:
                fused_emotion = "sad"
                stress_level = max(stress_level, 60) if stress_level > 50 else 60
                tone = "subdued"

        # 4. Check for contradiction between words and physical markers
        if has_positive_words and (stress_level > 65 or fused_emotion in ["sad", "anxious", "angry", "frustrated"]):
            contradiction_detected = True
            hidden_emotion = fused_emotion
            fused_emotion = "confused"

        # Special check: self-harm phrases override emotion to high-stress depressed/anxious
        if "kill myself" in text_lower or "suicide" in text_lower or "end my life" in text_lower:
            fused_emotion = "depressed"
            stress_level = 95
            tone = "flat" if tone == "calm" else tone

        # 5. Integrate Gaze Avoidance and Head Tilt cues
        if isinstance(video_features, dict) and video_features:
            if eye_contact_ratio < 0.50:
                stress_level = min(100, stress_level + 15)
                if tone in ["calm", "unknown"]:
                    tone = "avoidant"
            if head_pitch > 15.0:  # looking down
                stress_level = min(100, stress_level + 10)
                if fused_emotion in ["neutral", "calm"]:
                    fused_emotion = "sad"
                    tone = "subdued"

        # Assemble result
        result = {
            "emotion": fused_emotion,
            "stress_level": stress_level,
            "tone": tone,
            "contradiction_detected": contradiction_detected,
            "hidden_emotion": hidden_emotion
        }

        # Enrich result with raw telemetry (eye contact, head pose, etc.)
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
            from core.utils import parse_robust_json
            result = parse_robust_json(content)
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

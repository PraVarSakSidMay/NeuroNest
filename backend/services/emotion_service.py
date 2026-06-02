import json
from .model_manager import model_manager
from core.logger import logger

def analyze_emotion(transcript, audio_features, video_features=None):
    video_info = ""
    if video_features:
        video_info = f"\nVideo Facial Features:\n{json.dumps(video_features, indent=2)}\n"
        if video_features.get("timeline"):
            video_info += (
                "\nThe video features summarize the full recording window, not a single frame. "
                "Prioritize emotion_distribution, sample_count, eye_contact_ratio, head_pose, "
                "masking flags, and the timeline when deciding the user's actual emotional state.\n"
            )

    audio_hint = audio_features.get("audio_emotion_hint", "") if isinstance(audio_features, dict) else ""
    logger.info(
        "Emotion fusion input",
        transcript_preview=transcript[:120],
        audio_hint=audio_hint,
        audio_source=audio_features.get("source", "unknown") if isinstance(audio_features, dict) else "unknown",
        video_present=bool(video_features),
    )

    prompt = f"""
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
    {transcript}

    Audio Features:
    {audio_features}

    Audio Emotion Hint: {audio_hint}
    {video_info}

    Return JSON strictly in this format:
    {{
      "emotion": "string (the overarching fused emotion detected. MUST be one of: 'neutral', 'happy', 'sad', 'angry', 'anxious', 'fearful', 'surprised', 'disgusted', 'confused', 'excited', 'frustrated', 'depressed', 'calm')",
      "stress_level": 0-100 (integer representing stress level),
      "tone": "string (e.g., trembling, calm, aggressive)",
      "contradiction_detected": boolean (true if words or voice contradict the facial micro-expressions),
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

        result = json.loads(content)

        # Guard: LLM sometimes returns {} or an incomplete object for inaudible/empty audio.
        # Ensure all required keys are present, back-filling with safe defaults.
        required_keys = {"emotion", "stress_level", "tone", "contradiction_detected", "hidden_emotion"}
        if not isinstance(result, dict) or not required_keys.issubset(result.keys()):
            print(f"Emotion JSON missing required keys. Received: {result}")
            result = {
                "emotion": result.get("emotion", "neutral") if isinstance(result, dict) else "neutral",
                "stress_level": result.get("stress_level", 50) if isinstance(result, dict) else 50,
                "tone": result.get("tone", "unknown") if isinstance(result, dict) else "unknown",
                "contradiction_detected": result.get("contradiction_detected", False) if isinstance(result, dict) else False,
                "hidden_emotion": result.get("hidden_emotion", "") if isinstance(result, dict) else "",
            }
    except Exception as e:
        print(f"Error parsing emotion JSON: {e}. Raw content: {content}")
        result = {
            "emotion": "neutral",
            "stress_level": 50,
            "tone": "unknown",
            "contradiction_detected": False,
            "hidden_emotion": ""
        }

    # Merge visual attention telemetry for down-stream pacing services
    if video_features:
        result["eye_contact_ratio"] = video_features.get("eye_contact_ratio", 1.0)
        result["head_pose"] = video_features.get("head_pose", {"pitch": 0, "yaw": 0, "roll": 0})
        # Include a small subset of raw AUs if they are significant
        aus = video_features.get("actionUnits", {})
        if aus:
            result["notable_facial_markers"] = {k: v for k, v in aus.items() if v > 0.4}
    else:
        result["eye_contact_ratio"] = 1.0
        result["head_pose"] = {"pitch": 0, "yaw": 0, "roll": 0}

    # Add audio markers if present
    if isinstance(audio_features, dict):
        result["vocal_markers"] = {
            "pitch_variation": "high" if audio_features.get("pitch_std", 0) > 20 else "normal",
            "shaking": audio_features.get("is_trembling", False),
            "whispering": audio_features.get("is_whispering", False)
        }

    return result

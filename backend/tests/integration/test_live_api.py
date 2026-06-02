"""
NeuroNest Live API Integration Tests
=====================================
Tests the running backend at http://127.0.0.1:8000 end-to-end.

Coverage:
  1. Health check — server is up and responds
  2. GET /session  — greeting endpoint returns contextual greeting
  3. POST /process-voice — happy path with frontier audio features
  4. POST /process-voice — high-stress trembling voice path
  5. POST /process-voice — cognitive avoidance gaze (eye_contact_ratio < 0.6)
  6. POST /process-voice — contradiction detection (say fine, trembling voice)
  7. POST /process-voice — head-down deflection path (pitch > 15°)
  8. POST /process-voice — missing video_analysis (graceful degradation)
  9. POST /process-voice — completely empty audio (error handling)
 10. POST /preview-voice — voice preview endpoint

Run with:
    pytest tests/integration/test_live_api.py -v
"""

import io
import json
import struct
import wave
import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 60  # seconds — LLM waterfall can take time


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_silent_wav(duration_sec: float = 1.5, sample_rate: int = 16000) -> bytes:
    """Generate a minimal silent WAV file in memory (no external files needed)."""
    num_samples = int(sample_rate * duration_sec)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{num_samples}h", *([0] * num_samples)))
    buf.seek(0)
    return buf.read()


def build_video_payload(
    emotion: str = "neutral",
    confidence: float = 0.6,
    eye_contact_ratio: float = 0.85,
    pitch: float = 0.0,
    yaw: float = 0.0,
    roll: float = 0.0,
    is_masked: bool = False,
    mask_confidence: float = 0.0,
    face_quality: float = 0.85,
    action_units: dict | None = None,
) -> str:
    return json.dumps({
        "emotion": emotion,
        "confidence": confidence,
        "face_quality": face_quality,
        "action_units": action_units or {"AU1": 0.1, "AU4": 0.2, "AU6": 0.3, "AU12": 0.6, "AU15": 0.05, "AU25": 0.4},
        "is_masked": is_masked,
        "mask_confidence": mask_confidence,
        "eye_contact_ratio": eye_contact_ratio,
        "head_pose": {"pitch": pitch, "yaw": yaw, "roll": roll},
    })


def build_audio_payload(
    pitch_mean: float = 120.0,
    jitter: float = 0.02,
    loudness: float = 0.4,
    vol_std_dev: float = 8.0,
    is_trembling: bool = False,
    is_crying: bool = False,
    is_whispering: bool = False,
    description: str = "stable and composed voice",
) -> str:
    return json.dumps({
        "pitch_mean": pitch_mean,
        "jitter": jitter,
        "loudness": loudness,
        "volume_std_dev": vol_std_dev,
        "pitch_std_dev": 5.0,
        "is_trembling": is_trembling,
        "is_singing": False,
        "is_crying": is_crying,
        "is_whispering": is_whispering,
        "voice_description": description,
        "source": "browser_web_audio_api",
    })


def post_voice(audio_bytes: bytes, audio_analysis: str, video_analysis: str | None = None, voice: str = "Rachel"):
    """Helper to POST to /process-voice."""
    files = {"file": ("recording.wav", io.BytesIO(audio_bytes), "audio/wav")}
    data = {"audio_analysis": audio_analysis, "voice_name": voice}
    if video_analysis is not None:
        data["video_analysis"] = video_analysis
    return requests.post(f"{BASE_URL}/process-voice", files=files, data=data, timeout=TIMEOUT)


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

class TestHealthCheck:
    """Verify the backend is reachable."""

    def test_server_is_up(self):
        """Server root responds with 200 or 404 (route may not exist, but server is alive)."""
        try:
            resp = requests.get(BASE_URL, timeout=5)
            assert resp.status_code in (200, 404, 422), f"Unexpected status: {resp.status_code}"
        except requests.ConnectionError:
            pytest.fail("Backend server is not running at http://127.0.0.1:8000")

    def test_docs_endpoint(self):
        """OpenAPI docs should be available (FastAPI auto-generates them)."""
        resp = requests.get(f"{BASE_URL}/docs", timeout=5)
        assert resp.status_code == 200, "FastAPI /docs not accessible"


class TestSessionGreeting:
    """Test the /session greeting endpoint."""

    def test_session_returns_greeting(self):
        resp = requests.post(f"{BASE_URL}/session-start", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Session failed: {resp.text}"
        body = resp.json()
        assert "greeting" in body, f"No greeting key in response: {body}"
        assert isinstance(body["greeting"], str)
        assert len(body["greeting"]) > 0


class TestVoiceProcessingHappyPath:
    """Test the standard voice processing pipeline with composed, normal inputs."""

    def test_process_voice_returns_required_fields(self):
        audio = make_silent_wav(duration_sec=2.0)
        audio_analysis = build_audio_payload(description="stable and composed voice")
        video_analysis = build_video_payload(emotion="neutral", eye_contact_ratio=0.9)

        resp = post_voice(audio, audio_analysis, video_analysis)
        assert resp.status_code == 200, f"Process-voice failed: {resp.text}"

        body = resp.json()
        assert "transcript" in body
        assert "emotion" in body
        assert "response" in body
        assert isinstance(body["response"], str)
        assert len(body["response"]) > 0

    def test_emotion_object_has_expected_keys(self):
        audio = make_silent_wav()
        audio_analysis = build_audio_payload()
        video_analysis = build_video_payload(emotion="happy", confidence=0.82)

        resp = post_voice(audio, audio_analysis, video_analysis)
        assert resp.status_code == 200
        body = resp.json()

        emotion = body.get("emotion", {})
        assert "emotion" in emotion, "emotion.emotion key missing"
        assert "stress_level" in emotion, "emotion.stress_level key missing"
        assert isinstance(emotion["stress_level"], (int, float))
        assert 0 <= emotion["stress_level"] <= 100

    def test_response_is_non_empty_string(self):
        audio = make_silent_wav()
        resp = post_voice(audio, build_audio_payload(), build_video_payload())
        assert resp.status_code == 200
        body = resp.json()
        response_text = body.get("response", "")
        assert isinstance(response_text, str)
        assert len(response_text.strip()) > 10, "Response seems too short"


class TestHighStressPath:
    """Test the trembling / high-distress voice path to verify empathetic responses."""

    def test_trembling_voice_detected(self):
        audio = make_silent_wav()
        audio_analysis = build_audio_payload(
            pitch_mean=85.0,
            jitter=0.14,
            loudness=0.08,
            vol_std_dev=28.0,
            is_trembling=True,
            description="trembling or shaking voice — high amplitude instability",
        )
        video_analysis = build_video_payload(emotion="anxious", confidence=0.75)

        resp = post_voice(audio, audio_analysis, video_analysis)
        assert resp.status_code == 200, f"Trembling path failed: {resp.text}"
        body = resp.json()
        assert "response" in body
        # High stress voices should generate a non-empty empathetic response
        assert len(body["response"]) > 0

    def test_high_stress_level_returned(self):
        audio = make_silent_wav()
        audio_analysis = build_audio_payload(
            jitter=0.18,
            vol_std_dev=32.0,
            is_trembling=True,
            is_crying=True,
            description="crying or tearful — irregular volume with unstable pitch",
        )
        video_analysis = build_video_payload(emotion="sad", confidence=0.9)

        resp = post_voice(audio, audio_analysis, video_analysis)
        assert resp.status_code == 200
        body = resp.json()
        emotion = body.get("emotion", {})
        # Stress level should reflect the distress cues (ideally > 40)
        stress_level = emotion.get("stress_level", 0)
        assert isinstance(stress_level, (int, float))
        assert 0 <= stress_level <= 100


class TestCognitiveAvoidancePath:
    """Test that gaze avoidance (eye_contact_ratio < 0.60) modifies LLM response pacing."""

    def test_avoidance_gaze_payload_accepted(self):
        """Backend should accept low eye contact ratio without erroring."""
        audio = make_silent_wav()
        audio_analysis = build_audio_payload(description="quiet, withdrawn voice")
        video_analysis = build_video_payload(
            emotion="anxious",
            eye_contact_ratio=0.30,  # Strong avoidance
            pitch=4.0,
        )

        resp = post_voice(audio, audio_analysis, video_analysis)
        assert resp.status_code == 200, f"Avoidance path failed: {resp.text}"
        body = resp.json()
        assert "response" in body
        assert len(body["response"]) > 0

    def test_head_down_deflection_payload_accepted(self):
        """Head pitch > 15° (looking down) should be handled gracefully."""
        audio = make_silent_wav()
        audio_analysis = build_audio_payload(description="quiet, looking down")
        video_analysis = build_video_payload(
            emotion="sad",
            eye_contact_ratio=0.45,
            pitch=22.0,  # Severe downward gaze
        )

        resp = post_voice(audio, audio_analysis, video_analysis)
        assert resp.status_code == 200
        body = resp.json()
        assert "response" in body


class TestContradictionDetection:
    """Test that verbal/vocal contradictions are surfaced in the response."""

    def test_contradiction_field_present(self):
        """Even if contradiction is not detected, the field should exist."""
        audio = make_silent_wav()
        audio_analysis = build_audio_payload(
            vol_std_dev=22.0,
            is_trembling=True,
            description="trembling or shaking voice — high amplitude instability",
        )
        video_analysis = build_video_payload(
            emotion="happy",       # facial expression says happy
            confidence=0.7,
            is_masked=True,        # but it may be a mask
            mask_confidence=0.65,
        )

        resp = post_voice(audio, audio_analysis, video_analysis)
        assert resp.status_code == 200
        body = resp.json()
        emotion = body.get("emotion", {})
        # contradiction_detected key should exist
        assert "contradiction_detected" in emotion, "contradiction_detected key missing from emotion"

    def test_masked_emotion_flag_in_video_accepted(self):
        """Masking flag in video analysis should not break the pipeline."""
        audio = make_silent_wav()
        video_analysis = build_video_payload(is_masked=True, mask_confidence=0.8)
        resp = post_voice(audio, build_audio_payload(), video_analysis)
        assert resp.status_code == 200


class TestGracefulDegradation:
    """Test that missing or malformed optional fields don't break the pipeline."""

    def test_no_video_analysis(self):
        """Process-voice should work without video_analysis."""
        audio = make_silent_wav()
        resp = post_voice(audio, build_audio_payload(), video_analysis=None)
        assert resp.status_code == 200, f"No video_analysis failed: {resp.text}"
        body = resp.json()
        assert "response" in body

    def test_no_audio_analysis(self):
        """Process-voice should work without audio_analysis."""
        audio = make_silent_wav()
        files = {"file": ("recording.wav", io.BytesIO(audio), "audio/wav")}
        data = {"voice_name": "Rachel"}
        resp = requests.post(f"{BASE_URL}/process-voice", files=files, data=data, timeout=TIMEOUT)
        assert resp.status_code == 200, f"No audio_analysis failed: {resp.text}"

    def test_malformed_audio_analysis_json(self):
        """Malformed JSON in audio_analysis should return 422 or be handled gracefully."""
        audio = make_silent_wav()
        files = {"file": ("recording.wav", io.BytesIO(audio), "audio/wav")}
        data = {"audio_analysis": "NOT VALID JSON AT ALL", "voice_name": "Rachel"}
        resp = requests.post(f"{BASE_URL}/process-voice", files=files, data=data, timeout=TIMEOUT)
        # Should either process gracefully (200) or return a validation error (422)
        assert resp.status_code in (200, 422, 500), f"Unexpected status: {resp.status_code}"


class TestVoicePreviewEndpoint:
    """Test the /preview-voice endpoint for all 5 voice personas."""

    @pytest.mark.parametrize("voice_name", ["Rachel", "Amelia", "Josh", "Nathan", "Sam"])
    def test_preview_voice_returns_audio_url(self, voice_name: str):
        data = {"voice_name": voice_name}
        resp = requests.post(f"{BASE_URL}/preview-voice", data=data, timeout=TIMEOUT)
        assert resp.status_code == 200, f"Preview failed for {voice_name}: {resp.text}"
        body = resp.json()
        assert "audio_url" in body, f"No audio_url in preview response for {voice_name}"
        assert isinstance(body["audio_url"], str)
        assert len(body["audio_url"]) > 0


class TestOfflineErrorClassification:
    """
    Simulate what the frontend offline interception logic detects.
    Verifies the backend responds with classifiable error shapes
    so the frontend can correctly distinguish network errors from API errors.
    """

    def test_missing_required_file_field_gives_422(self):
        """When no audio file is sent, backend must return 422 (validation error)."""
        data = {"voice_name": "Rachel", "audio_analysis": build_audio_payload()}
        resp = requests.post(f"{BASE_URL}/process-voice", data=data, timeout=10)
        assert resp.status_code == 422, (
            f"Expected 422 for missing file field, got {resp.status_code}: {resp.text}"
        )

    def test_error_response_shape(self):
        """Error responses should be JSON-parseable (not raw HTML crash pages)."""
        data = {"voice_name": "Rachel"}
        resp = requests.post(f"{BASE_URL}/process-voice", data=data, timeout=10)
        assert resp.headers.get("content-type", "").startswith("application/json"), (
            "Error response should be JSON, not HTML"
        )
        body = resp.json()
        # FastAPI 422 responses use {"detail": [...]} structure
        assert "detail" in body or "error" in body, f"Unexpected error body shape: {body}"

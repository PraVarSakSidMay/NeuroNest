import pytest
from unittest.mock import patch, MagicMock
from services.opensmile_service import extract_audio_features

def test_extract_audio_features_from_frontend():
    # Verify that if frontend features are provided, they are returned directly
    frontend_features = {
        "pitch_mean": 210.5,
        "jitter": 0.03,
        "loudness": 0.25,
        "volume_std_dev": 0.02,
        "pitch_std_dev": 5.0,
        "is_trembling": True,
        "is_singing": False,
        "is_crying": False,
        "is_whispering": False,
        "voice_description": "quivering voice",
    }
    
    result = extract_audio_features("dummy_path.webm", frontend_features)
    
    assert result["source"] == "browser_web_audio_api"
    assert result["pitch_mean"] == 210.5
    assert result["jitter"] == 0.03
    assert result["loudness"] == 0.25
    assert result["is_trembling"] is True
    assert result["voice_description"] == "quivering voice"
    assert isinstance(result["audio_emotion_hint"], str)


@patch("services.opensmile_service.smile", None)  # Mock opensmile missing
@patch("builtins.__import__", side_effect=ImportError)  # Mock librosa missing
@patch("subprocess.run", side_effect=Exception("ffmpeg missing"))  # Mock ffmpeg missing
def test_extract_audio_features_ultimate_fallback(mock_run, mock_import):
    # Verify that when all processing libraries and tools are missing, it returns the mock fallback
    result = extract_audio_features("dummy_path.webm", None)
    
    assert result["source"] == "mock"
    assert result["pitch_mean"] == 60.5
    assert result["jitter"] == 0.05
    assert result["loudness"] == 0.15
    assert result["is_trembling"] is False
    assert result["audio_emotion_hint"] == ""

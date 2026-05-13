"""
Audio Feature Extraction
========================
Priority chain:
  1. Real browser Web Audio API features (from frontend) — always accurate
  2. openSMILE local analysis — if mediainfo/ffmpeg available
  3. librosa analysis — Python-only fallback
  4. Mock features — last resort, clearly flagged
"""

import opensmile
import os

smile = opensmile.Smile(
    feature_set=opensmile.FeatureSet.eGeMAPSv02,
    feature_level=opensmile.FeatureLevel.Functionals,
)

def extract_audio_features(audio_path: str, frontend_features: dict = None) -> dict:

    # ── Priority 1: Real browser-measured features ─────────────────────
    # The frontend uses Web Audio API to measure pitch, volume, trembling,
    # crying patterns, and singing patterns in real time. This is the most
    # accurate representation of the actual voice state.
    if frontend_features and isinstance(frontend_features, dict):
        print(f"Audio: Using real browser Web Audio API features. Voice: {frontend_features.get('voice_description', 'N/A')}")
        return {
            "pitch_mean": frontend_features.get("pitch_mean", 60.5),
            "jitter": frontend_features.get("jitter", 0.05),
            "loudness": frontend_features.get("loudness", 0.15),
            "volume_std_dev": frontend_features.get("volume_std_dev", 0),
            "pitch_std_dev": frontend_features.get("pitch_std_dev", 0),
            "is_trembling": frontend_features.get("is_trembling", False),
            "is_singing": frontend_features.get("is_singing", False),
            "is_crying": frontend_features.get("is_crying", False),
            "is_whispering": frontend_features.get("is_whispering", False),
            "voice_description": frontend_features.get("voice_description", "stable voice"),
            "source": "browser_web_audio_api"
        }

    # ── Priority 2: openSMILE local analysis ───────────────────────────
    try:
        features = smile.process_file(audio_path)
        pitch = float(features["F0semitoneFrom27.5Hz_sma3nz_amean"][0])
        jitter = float(features["jitterLocal_sma3nz_amean"][0])
        loudness = float(features["loudness_sma3_amean"][0])
        print("Audio: openSMILE features extracted successfully")
        return {
            "pitch_mean": pitch,
            "jitter": jitter,
            "loudness": loudness,
            "volume_std_dev": 0,
            "pitch_std_dev": 0,
            "is_trembling": jitter > 0.05,
            "is_singing": False,
            "is_crying": jitter > 0.07 and loudness < 0.3,
            "is_whispering": loudness < 0.1,
            "voice_description": _describe(pitch, jitter, loudness),
            "source": "opensmile"
        }
    except Exception as e:
        print(f"Audio: openSMILE unavailable ({type(e).__name__}), trying librosa...")

    # ── Priority 3: librosa Python analysis ────────────────────────────
    try:
        import librosa
        import numpy as np
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        rms = float(np.mean(librosa.feature.rms(y=y)))
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=y)))
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = pitches[magnitudes > np.max(magnitudes) * 0.1]
        pitch_mean = float(np.mean(pitch_values)) if len(pitch_values) > 0 else 60.0
        pitch_std = float(np.std(pitch_values)) if len(pitch_values) > 0 else 0.0
        jitter_est = zcr  # zero crossing rate is a rough jitter proxy
        print("Audio: librosa features extracted successfully")
        return {
            "pitch_mean": round(pitch_mean, 2),
            "jitter": round(jitter_est, 4),
            "loudness": round(rms, 4),
            "volume_std_dev": 0,
            "pitch_std_dev": round(pitch_std, 2),
            "is_trembling": jitter_est > 0.1,
            "is_singing": pitch_std > 50 and rms > 0.05,
            "is_crying": jitter_est > 0.08 and rms < 0.15,
            "is_whispering": rms < 0.02,
            "voice_description": _describe(pitch_mean, jitter_est, rms),
            "source": "librosa"
        }
    except Exception as e:
        print(f"Audio: librosa failed ({type(e).__name__}), using mock features")

    # ── Priority 4: Mock fallback ───────────────────────────────────────
    print("Audio: WARNING — using mock features. Install mediainfo for real analysis.")
    return {
        "pitch_mean": 60.5,
        "jitter": 0.05,
        "loudness": 0.15,
        "volume_std_dev": 0,
        "pitch_std_dev": 0,
        "is_trembling": False,
        "is_singing": False,
        "is_crying": False,
        "is_whispering": False,
        "voice_description": "voice analysis unavailable — using defaults",
        "source": "mock"
    }


def _describe(pitch, jitter, loudness) -> str:
    parts = []
    if jitter > 0.08: parts.append("trembling or unstable voice")
    if loudness < 0.1: parts.append("very quiet/whispering")
    if pitch > 100: parts.append("high-pitched voice suggesting stress")
    if not parts: parts.append("stable, composed voice")
    return "; ".join(parts)

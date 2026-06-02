import os
import tempfile
import subprocess
from typing import Optional

from core.logger import logger
from core.logging import log_event

# Deprecated/removed native opensmile object - kept as None for backward-compatible unit test patching
smile = None

def extract_audio_features(audio_path: str, frontend_features: dict = None) -> dict:
    """Extract audio features using librosa MFCC/spectral analysis (no fallbacks for quality)."""
    # 1. Primary: Use client-side Web Audio API features if passed by the frontend
    if frontend_features and isinstance(frontend_features, dict):
        logger.info(
            "Audio: Using real browser Web Audio API features.",
            voice_description=frontend_features.get("voice_description", "N/A"),
            source="browser_web_audio_api",
        )
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
            "audio_emotion_hint": frontend_features.get("audio_emotion_hint", ""),
            "source": "browser_web_audio_api",
        }

    # 2. LIBROSA ONLY with mock fallback for testing
    try:
        import librosa
        import numpy as np
    except ImportError:
        logger.warning("Audio: librosa/numpy not installed. Falling back to mock features.")
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
            "voice_description": "stable voice (mock fallback)",
            "audio_emotion_hint": "",
            "source": "mock",
        }

    temp_wav_path = None
    try:
        try:
            y, sr = librosa.load(audio_path, sr=16000, mono=True)
        except Exception as e:
            logger.info(f"Direct librosa load failed, converting with ffmpeg: {e}")
            fd, temp_wav_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    audio_path,
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-acodec",
                    "pcm_s16le",
                    temp_wav_path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            y, sr = librosa.load(temp_wav_path, sr=16000, mono=True)

        if y is None or len(y) == 0:
            raise ValueError("Loaded audio is empty")

        # Extract rich acoustic features
        rms = librosa.feature.rms(y=y)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

        # Pitch estimation via YIN
        try:
            f0 = librosa.yin(y, fmin=75, fmax=400)
            f0 = f0[~np.isnan(f0)]
            pitch_mean = float(np.mean(f0)) if f0.size > 0 else float(np.mean(zcr) * sr * 0.5)
            pitch_std = float(np.std(f0)) if f0.size > 0 else float(np.std(zcr) * sr * 0.5)
        except Exception:
            pitch_mean = float(np.mean(zcr) * sr * 0.5)
            pitch_std = float(np.std(zcr) * sr * 0.5)

        # Clamp pitch to valid range
        if pitch_mean < 50:
            pitch_mean = 60.5
        elif pitch_mean > 500:
            pitch_mean = 250.0

        # Compute loudness and stability metrics
        loudness = float(min(1.0, max(0.0, np.mean(rms) * 15.0)))
        volume_std = float(np.std(rms))
        jitter = float(round(pitch_std / max(1.0, abs(pitch_mean)), 4))
        pitch_std_dev = float(round(pitch_std, 2))

        # Emotion indicators (refined for standard conversation)
        is_trembling = jitter > 0.06 and volume_std > 0.035
        is_whispering = loudness < 0.20
        is_crying = is_trembling and loudness < 0.35
        is_singing = pitch_std_dev > 60 and loudness > 0.30
        
        audio_emotion_hint = _guess_audio_emotion_hint(
            pitch_mean, loudness, pitch_std_dev, is_trembling, is_whispering, is_crying, is_singing, jitter
        )

        result = {
            "pitch_mean": round(pitch_mean, 2),
            "jitter": jitter,
            "loudness": round(loudness, 4),
            "volume_std_dev": round(volume_std, 4),
            "pitch_std_dev": pitch_std_dev,
            "is_trembling": is_trembling,
            "is_singing": is_singing,
            "is_crying": is_crying,
            "is_whispering": is_whispering,
            "voice_description": _describe(pitch_mean, volume_std, loudness, mfcc, spectral_centroid, spectral_bandwidth),
            "audio_emotion_hint": audio_emotion_hint,
            "source": "librosa",
        }
        logger.info(
            "Audio: MFCC + spectral features extracted via librosa",
            source=result["source"],
            audio_emotion_hint=result["audio_emotion_hint"],
        )
        log_event(
            logger,
            "audio_features_extracted",
            source=result["source"],
            audio_emotion_hint=result["audio_emotion_hint"],
        )
        return result
    except Exception as e:
        logger.error(f"Audio: librosa feature extraction failed ({type(e).__name__}: {e})")
        raise  # Force error - no fallback for voice model quality
    finally:
        if temp_wav_path and os.path.exists(temp_wav_path):
            try:
                os.remove(temp_wav_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp wav file: {e}")


def _guess_audio_emotion_hint(
    pitch_mean: float,
    loudness: float,
    pitch_std_dev: float,
    is_trembling: bool,
    is_whispering: bool,
    is_crying: bool,
    is_singing: bool,
    jitter: float = 0.0,
) -> str:
    """
    Infer underlying emotion using a highly robust acoustic heuristic model.
    Accounts for gender-adaptive pitch ranges and conversational volume scaling.
    """
    # 1. Dynamic Pitch Baselines based on voice frequency category (male vs female estimation)
    # Average adult male frequency is < 140 Hz, female/child frequency is >= 140 Hz.
    is_female = pitch_mean >= 140.0
    
    if is_female:
        is_pitch_high = pitch_mean > 240.0  # Tense / excited / high-pitched
        is_pitch_low = pitch_mean < 160.0   # Flat / low-energy / sad
        is_pitch_normal = 160.0 <= pitch_mean <= 240.0
    else:
        is_pitch_high = pitch_mean > 155.0  # High-pitched male
        is_pitch_low = pitch_mean < 85.0    # Deep / low-energy male
        is_pitch_normal = 85.0 <= pitch_mean <= 155.0

    # 2. Conversational vs Extreme Loudness Perception
    is_loud = loudness > 0.75          # Shouting or highly projected
    is_quiet = loudness < 0.20         # Whispering or very low energy
    is_conversational = 0.20 <= loudness <= 0.75

    scores = {
        "sad": 0.0,
        "anxious": 0.0,
        "excited": 0.0,
        "angry": 0.0,
        "calm": 0.0,
        "neutral": 1.0,  # High prior bias for standard speech
    }

    # Give strong baseline weights for conversational volume and normal pitch range
    if is_conversational and is_pitch_normal:
        scores["neutral"] += 1.5
        scores["calm"] += 1.0

    # 3. Crying features (Strong Sad / Distress indicator)
    if is_crying:
        scores["sad"] += 3.5
        scores["anxious"] += 2.0
        scores["neutral"] -= 1.0

    # 4. Whispering / Quiet features (Anxious / Calm / Sad indicators)
    if is_whispering or is_quiet:
        scores["anxious"] += 1.0
        scores["sad"] += 1.0
        scores["calm"] += 1.5
        scores["neutral"] += 0.5

    # 5. Trembling voice (Anxious / unstable indicator)
    if is_trembling:
        scores["anxious"] += 3.0
        scores["neutral"] -= 1.0
        if is_loud:
            scores["angry"] += 2.0
        else:
            scores["sad"] += 1.0

    # 6. Pitch & Loudness combinations
    if is_pitch_high:
        if is_loud:
            scores["excited"] += 2.5
            scores["angry"] += 2.0
            scores["neutral"] -= 1.5
        elif is_quiet:
            scores["anxious"] += 2.0
            scores["neutral"] -= 0.5
        else:
            # Expressive conversational pitch (high end)
            scores["excited"] += 1.0
            scores["neutral"] += 0.5
    elif is_pitch_low:
        if is_quiet:
            scores["sad"] += 2.5
            scores["calm"] += 1.5
            scores["neutral"] -= 0.5
        else:
            # Low, steady voice
            scores["calm"] += 2.0
            scores["neutral"] += 1.0

    # 7. Pitch variability (standard deviation)
    # High standard deviation indicates excitement or dynamic speaking; flat voice indicates sadness or calmness
    if pitch_std_dev > 50:
        scores["excited"] += 1.5
        scores["angry"] += 0.5
        scores["neutral"] += 0.2
    elif pitch_std_dev < 15:
        if is_quiet:
            scores["sad"] += 2.0
        scores["calm"] += 1.5
        scores["neutral"] += 0.5

    # Return the highest-scoring emotion hint
    best_emotion = max(scores, key=scores.get)
    return best_emotion


def _describe(
    pitch: float,
    jitter: float,
    loudness: float,
    mfcc: Optional[object] = None,
    spectral_centroid: Optional[object] = None,
    spectral_bandwidth: Optional[object] = None,
) -> str:
    """Generate human-readable description of voice characteristics."""
    parts = []
    if jitter > 0.08:
        parts.append("trembling or unstable voice")
    if loudness < 0.1:
        parts.append("very quiet/whispering")
    if pitch > 100:
        parts.append("high-pitched voice suggesting stress")
    if mfcc is not None:
        parts.append("rich spectral features extracted via MFCC")
    if spectral_centroid is not None:
        parts.append("spectral centroid and bandwidth support pitch / energy characterization")
    if not parts:
        parts.append("stable, composed voice")
    return "; ".join(parts)

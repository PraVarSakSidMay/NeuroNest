import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Paths
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(DATA_DIR, "raw_images")
TASK_FILE = "c:/Users/Dell/Downloads/VoiceAssistant/frontend/public/models/face_landmarker.task"

# Refined weights and biases optimized for 13 emotions
PROFILES = {
    "happy": {
        "features": {
            "cheekSquintLeft": 3.0, "cheekSquintRight": 3.0,
            "mouthSmileLeft": 6.0, "mouthSmileRight": 6.0,
            "mouthDimpleLeft": 1.5, "mouthDimpleRight": 1.5,
            "browDownLeft": -3.0, "browDownRight": -3.0,
            "mouthFrownLeft": -5.0, "mouthFrownRight": -5.0,
        },
        "bias": -1.0,
    },
    "sad": {
        "features": {
            "browInnerUp": 5.0,
            "mouthFrownLeft": 5.0, "mouthFrownRight": 5.0,
            "mouthShrugLower": 3.0, # chin raise
            "mouthSmileLeft": -6.0, "mouthSmileRight": -6.0,
            "browDownLeft": 1.5, "browDownRight": 1.5,
            "mouthLowerDownLeft": 2.0, "mouthLowerDownRight": 2.0,
        },
        "bias": -0.5,
    },
    "angry": {
        "features": {
            "browDownLeft": 6.0, "browDownRight": 6.0,
            "eyeSquintLeft": 3.0, "eyeSquintRight": 3.0,
            "mouthPressLeft": 3.0, "mouthPressRight": 3.0,
            "mouthSmileLeft": -5.0, "mouthSmileRight": -5.0,
            "jawForward": 2.0,
            "noseSneerLeft": -2.0, "noseSneerRight": -2.0,
        },
        "bias": -1.0, # Slightly higher bias to ensure angry can trigger
    },
    "fearful": {
        "features": {
            "browInnerUp": 4.0,
            "browOuterUpLeft": 3.0, "browOuterUpRight": 3.0,
            "eyeWideLeft": 5.0, "eyeWideRight": 5.0,
            "jawOpen": 3.0,
            "mouthStretchLeft": 3.0, "mouthStretchRight": 3.0,
            "mouthSmileLeft": -4.0, "mouthSmileRight": -4.0,
        },
        "bias": -2.0,
    },
    "anxious": {
        "features": {
            "browInnerUp": 3.5,
            "browDownLeft": 2.5, "browDownRight": 2.5,
            "mouthFrownLeft": 3.0, "mouthFrownRight": 3.0,
            "mouthPressLeft": 2.5, "mouthPressRight": 2.5,
            "mouthSmileLeft": -4.0, "mouthSmileRight": -4.0,
            "mouthPucker": 1.5,
        },
        "bias": -1.5,
    },
    "surprised": {
        "features": {
            "browOuterUpLeft": 6.0, "browOuterUpRight": 6.0,
            "eyeWideLeft": 5.0, "eyeWideRight": 5.0,
            "jawOpen": 4.0,
            "browDownLeft": -4.0, "browDownRight": -4.0,
            "mouthSmileLeft": -2.0, "mouthSmileRight": -2.0,
        },
        "bias": -1.0,
    },
    "disgusted": {
        "features": {
            "noseSneerLeft": 6.0, "noseSneerRight": 6.0,
            "mouthUpperUpLeft": 6.0, "mouthUpperUpRight": 6.0,
            "mouthFrownLeft": 3.0, "mouthFrownRight": 3.0,
            "browDownLeft": 2.0, "browDownRight": 2.0,
            "eyeSquintLeft": 2.0, "eyeSquintRight": 2.0,
        },
        "bias": -1.0,
    },
    "confused": {
        "features": {
            "browInnerUp": 2.5,
            "browDownLeft": 2.0, "browDownRight": -1.0,
            "browOuterUpLeft": -1.0, "browOuterUpRight": 2.0,
            "mouthPucker": 2.0,
            "mouthLeft": 2.5, "mouthRight": 2.5,
            "mouthSmileLeft": -2.0, "mouthSmileRight": -2.0,
        },
        "bias": -2.0,
    },
    "excited": {
        "features": {
            "cheekSquintLeft": 3.0, "cheekSquintRight": 3.0,
            "mouthSmileLeft": 5.0, "mouthSmileRight": 5.0,
            "jawOpen": 3.0,
            "eyeWideLeft": 3.0, "eyeWideRight": 3.0,
            "mouthFrownLeft": -5.0, "mouthFrownRight": -5.0,
        },
        "bias": -2.0,
    },
    "frustrated": {
        "features": {
            "browDownLeft": 5.0, "browDownRight": 5.0,
            "mouthFrownLeft": 3.5, "mouthFrownRight": 3.5,
            "mouthPressLeft": 3.0, "mouthPressRight": 3.0,
            "mouthSmileLeft": -4.0, "mouthSmileRight": -4.0,
            "eyeSquintLeft": 2.0, "eyeSquintRight": 2.0,
        },
        "bias": -1.5,
    },
    "depressed": {
        "features": {
            "browInnerUp": 4.5,
            "mouthFrownLeft": 4.5, "mouthFrownRight": 4.5,
            "eyeBlinkLeft": 4.0, "eyeBlinkRight": 4.0,
            "mouthSmileLeft": -5.5, "mouthSmileRight": -5.5,
            "mouthLowerDownLeft": 2.0, "mouthLowerDownRight": 2.0,
        },
        "bias": -1.0,
    },
    "calm": {
        "features": {
            "mouthSmileLeft": -2.0, "mouthSmileRight": -2.0,
            "mouthFrownLeft": -2.0, "mouthFrownRight": -2.0,
            "browInnerUp": -2.0,
            "browDownLeft": -2.0, "browDownRight": -2.0,
            "eyeWideLeft": -2.0, "eyeWideRight": -2.0,
            "noseSneerLeft": -2.0, "noseSneerRight": -2.0,
            "jawOpen": -2.0,
        },
        "bias": 1.2,
    },
    "neutral": {
        "features": {
            "mouthSmileLeft": -2.0, "mouthSmileRight": -2.0,
            "mouthFrownLeft": -2.0, "mouthFrownRight": -2.0,
            "browInnerUp": -2.0,
            "browDownLeft": -2.0, "browDownRight": -2.0,
            "eyeWideLeft": -2.0, "eyeWideRight": -2.0,
            "jawOpen": -2.0,
            "noseSneerLeft": -2.0, "noseSneerRight": -2.0,
        },
        "bias": 1.0,
    },
}

def classify(bs):
    logits = {}
    
    # Calculate base logits
    for emotion, profile in PROFILES.items():
        logit = profile["bias"]
        for shape, weight in profile["features"].items():
            logit += weight * bs.get(shape, 0)
        logits[emotion] = logit

    # Apply overrides (Logical Gating Rules)
    get_val = lambda k: bs.get(k, 0)
    
    smile_val = (get_val("mouthSmileLeft") + get_val("mouthSmileRight")) / 2
    eye_wide = (get_val("eyeWideLeft") + get_val("eyeWideRight")) / 2
    jaw_open = get_val("jawOpen")
    
    # Merge cheekSquint and eyeSquint for robust smile validation
    eye_narrowing = max(
        get_val("cheekSquintLeft"), get_val("cheekSquintRight"),
        get_val("eyeSquintLeft"), get_val("eyeSquintRight")
    )
    
    brow_inner_up = get_val("browInnerUp")
    brow_down = (get_val("browDownLeft") + get_val("browDownRight")) / 2
    nose_sneer = (get_val("noseSneerLeft") + get_val("noseSneerRight")) / 2
    mouth_upper_up = (get_val("mouthUpperUpLeft") + get_val("mouthUpperUpRight")) / 2
    mouth_press = (get_val("mouthPressLeft") + get_val("mouthPressRight")) / 2
    mouth_roll = (get_val("mouthRollUpper") + get_val("mouthRollLower")) / 2

    # 1. Disgust-Smile Override (Resolves user's main edge case)
    disgust_factor = max(nose_sneer, mouth_upper_up)
    if disgust_factor > 0.12:
        # Boost disgust
        logits["disgusted"] += disgust_factor * 12.0
        # Penalize happy/excited heavily so disgust wins
        logits["happy"] -= disgust_factor * 15.0
        logits["excited"] -= disgust_factor * 15.0

    # 2. Upper-Face Validation for Happy (Prevents lip-sync/talking false positives)
    if smile_val > 0.12:
        # True happiness needs eye narrowing (squint) or a very strong smile (> 0.5)
        if eye_narrowing > 0.15 or smile_val > 0.5:
            logits["happy"] += smile_val * 4.0
        else:
            # Speaking / fake smile: penalize happy and excited
            logits["happy"] -= 4.0
            logits["excited"] -= 4.0

    # 3. Excited vs Happy vs Surprised separation:
    if smile_val > 0.25:
        if eye_wide > 0.15 or jaw_open > 0.25:
            logits["excited"] += 4.0
            logits["surprised"] -= 5.0
            logits["happy"] -= 2.0
        else:
            logits["happy"] += 3.0
            logits["excited"] -= 2.0
            logits["surprised"] -= 5.0

    # 4. Upper-Face Validation for Sad/Depressed (Prevents speech mouth frown false positives)
    mouth_frown = (get_val("mouthFrownLeft") + get_val("mouthFrownRight")) / 2
    mouth_shrug = get_val("mouthShrugLower") # chin raise
    
    if (mouth_frown > 0.2 or mouth_shrug > 0.2):
        if brow_inner_up > 0.12 or get_val("eyeBlinkLeft") > 0.3 or get_val("eyeBlinkRight") > 0.3:
            # Valid sadness
            logits["sad"] += 2.0
            logits["depressed"] += 2.0
        else:
            # Just talking: suppress sad/depressed
            logits["sad"] -= 5.0
            logits["depressed"] -= 5.0

    # 5. Upper-Face Validation for Angry/Frustrated (Prevents speech lip press false positives)
    # Angry/Frustrated MUST have lowered brows OR clear mouth rolling/pressing
    if brow_down < 0.12 and mouth_press < 0.15 and mouth_roll < 0.15:
        logits["angry"] -= 5.0
        logits["frustrated"] -= 5.0

    # 6. Sad vs Anxious vs Fearful:
    if eye_wide > 0.25 and jaw_open > 0.15:
        logits["fearful"] += 4.0
        logits["sad"] -= 4.0
        logits["anxious"] -= 4.0
        logits["depressed"] -= 4.0

    # 7. Asymmetry (Confusion):
    brow_asymmetry = abs(get_val("browDownLeft") - get_val("browDownRight")) + \
                     abs(get_val("browOuterUpLeft") - get_val("browOuterUpRight"))
    mouth_asymmetry = abs(get_val("mouthSmileLeft") - get_val("mouthSmileRight")) + \
                      abs(get_val("mouthPressLeft") - get_val("mouthPressRight"))
    
    # Exclude mouthPucker from asymmetry check (it's symmetric)
    skew_val = max(get_val("mouthLeft"), get_val("mouthRight"))
    if brow_asymmetry > 0.25 or mouth_asymmetry > 0.25 or skew_val > 0.25:
        logits["confused"] += (brow_asymmetry + mouth_asymmetry + skew_val) * 4.0

    # 8. Calm Active Verification:
    # Calm only triggers if the face is actively flat and expressive features are near zero.
    max_expressive = max(
        smile_val,
        mouth_frown,
        brow_down,
        brow_inner_up,
        disgust_factor,
        eye_wide,
        eye_narrowing,
        get_val("mouthPucker")
    )
    if max_expressive < 0.12:
        logits["calm"] += (0.12 - max_expressive) * 15.0
    else:
        logits["calm"] -= 5.0

    # Softmax
    max_logit = max(logits.values())
    exps = {e: np.exp(val - max_logit) for e, val in logits.items()}
    sum_exp = sum(exps.values())
    probs = {e: round(val / sum_exp, 4) for e, val in exps.items()}
    
    sorted_probs = sorted(probs.items(), key=lambda item: item[1], reverse=True)
    return sorted_probs[0], sorted_probs[:3]

def run_tests():
    # Initialize MediaPipe detector
    base_options = python.BaseOptions(model_asset_path=TASK_FILE)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=True,
        num_faces=1
    )
    detector = vision.FaceLandmarker.create_from_options(options)

    # Labeled candidates (Using correct angry scowling image from backend root)
    test_cases = {
        "happy": os.path.join(RAW_DIR, "happy_candidate_0.jpg"),
        "sad": os.path.join(RAW_DIR, "sad_candidate_0.jpg"),
        "angry": os.path.join(BACKEND_DIR, "test_photo-1509460913899-515f1df34fea.jpg"),
        "surprised": os.path.join(RAW_DIR, "surprised_candidate_0.jpg"),
        "disgusted": os.path.join(RAW_DIR, "disgusted_candidate_2.jpg"),
        "neutral": os.path.join(RAW_DIR, "neutral_candidate_0.jpg")
    }

    print("--- Evaluating optimized classifier rules on reference images ---")
    correct = 0
    total = 0
    for expected_emotion, path in test_cases.items():
        if not os.path.exists(path):
            print(f"File not found: {path}")
            continue
        total += 1
        
        bgr_image = cv2.imread(path)
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        
        detection_result = detector.detect(mp_image)
        blendshapes = detection_result.face_blendshapes[0]
        scores = {category.category_name: category.score for category in blendshapes}
        
        best, top_3 = classify(scores)
        predicted_emotion, prob = best
        
        # Accept depressed/sad or angry/frustrated as valid overlaps
        status = "FAIL"
        if predicted_emotion == expected_emotion:
            status = "PASS"
        elif expected_emotion == "sad" and predicted_emotion == "depressed":
            status = "PASS (clinical matches)"
        elif expected_emotion == "angry" and predicted_emotion == "frustrated":
            status = "PASS (clinical matches)"
            
        if "PASS" in status:
            correct += 1
            
        print(f"Target: {expected_emotion.upper():<10} -> Predicted: {predicted_emotion.upper():<10} ({prob:.2f}) | {status}")
        print("  Top 3 logits/probs:")
        for e, p in top_3:
            print(f"    - {e}: {p:.4f}")
        print("-" * 50)
        
    print(f"Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")

if __name__ == "__main__":
    run_tests()

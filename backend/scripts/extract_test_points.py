import os
import requests
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Predefined candidate Unsplash URLs to ensure high-quality detection for each emotion
IMAGE_CANDIDATES = {
    "happy": [
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=500&q=80",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=500&q=80"
    ],
    "sad": [
        "https://images.unsplash.com/photo-1516585427167-9f4af9627e6c?auto=format&fit=crop&w=500&q=80",
        "https://images.unsplash.com/photo-1499557354967-2b2d8910bcca?auto=format&fit=crop&w=500&q=80"
    ],
    "angry": [
        "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?auto=format&fit=crop&w=500&q=80",
        "https://images.unsplash.com/photo-1568602471122-7832951cc4c5?auto=format&fit=crop&w=500&q=80"
    ],
    "surprised": [
        "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?auto=format&fit=crop&w=500&q=80",
        "https://images.unsplash.com/photo-1504198453319-5ce911bafcde?auto=format&fit=crop&w=500&q=80"
    ],
    "disgusted": [
        "https://images.unsplash.com/photo-1594744803329-e58b31de215f?auto=format&fit=crop&w=500&q=80",
        "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?auto=format&fit=crop&w=500&q=80",
        "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?auto=format&fit=crop&w=500&q=80"
    ],
    "neutral": [
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=500&q=80",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=500&q=80"
    ]
}

# Paths
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
RAW_DIR = os.path.join(DATA_DIR, "raw_images")
TASK_FILE = "c:/Users/Dell/Downloads/VoiceAssistant/frontend/public/models/face_landmarker.task"

# Ensure directories exist
os.makedirs(RAW_DIR, exist_ok=True)

def download_and_detect():
    # Initialize MediaPipe detector
    if not os.path.exists(TASK_FILE):
        print(f"Error: task file not found at {TASK_FILE}")
        return

    base_options = python.BaseOptions(model_asset_path=TASK_FILE)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=True,
        num_faces=1
    )
    detector = vision.FaceLandmarker.create_from_options(options)

    results_summary = {}

    print("--- Downloading and analyzing emotion images ---")
    for emotion, urls in IMAGE_CANDIDATES.items():
        detected = False
        for idx, url in enumerate(urls):
            target_path = os.path.join(RAW_DIR, f"{emotion}_candidate_{idx}.jpg")
            try:
                # Download image
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    continue
                with open(target_path, "wb") as f:
                    f.write(response.content)

                # Process image
                bgr_image = cv2.imread(target_path)
                if bgr_image is None:
                    continue
                rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                
                # Detect face & landmarks
                detection_result = detector.detect(mp_image)
                if not detection_result.face_blendshapes:
                    continue
                
                # Success! Extract scores
                blendshapes = detection_result.face_blendshapes[0]
                scores = {category.category_name: round(category.score, 4) for category in blendshapes}
                
                # Clean up: keep non-zero entries
                active_scores = {k: v for k, v in scores.items() if v > 0.05}
                sorted_active = sorted(active_scores.items(), key=lambda item: item[1], reverse=True)
                
                results_summary[emotion] = sorted_active
                detected = True
                
                print(f"\n[SUCCESS] '{emotion}' face detected (candidate {idx})!")
                print(f"Top active blendshapes for '{emotion}':")
                for shape, val in sorted_active[:12]:
                    print(f"  {shape}: {val}")
                print("-" * 50)
                break # Move to next emotion
                
            except Exception as e:
                print(f"Error processing {emotion} candidate {idx}: {e}")
        
        if not detected:
            print(f"[FAILED] Could not detect a valid face for emotion '{emotion}' among all candidates.")

    # Write summary log
    summary_path = os.path.join(DATA_DIR, "blendshape_test_summary.txt")
    with open(summary_path, "w") as f:
        f.write("Extracted Blendshape Points for Emotion Reference Images\n")
        f.write("=" * 60 + "\n\n")
        for emotion, shapes in results_summary.items():
            f.write(f"Emotion: {emotion.upper()}\n")
            f.write("-" * 40 + "\n")
            for shape, val in shapes:
                f.write(f"{shape}: {val}\n")
            f.write("\n" + "=" * 60 + "\n\n")
    print(f"\nSaved full blendshape point logs to: {summary_path}")

if __name__ == "__main__":
    download_and_detect()

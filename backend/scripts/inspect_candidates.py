import os
import cv2
import glob
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Paths
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
RAW_DIR = os.path.join(DATA_DIR, "raw_images")
TASK_FILE = "c:/Users/Dell/Downloads/VoiceAssistant/frontend/public/models/face_landmarker.task"

def inspect():
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

    # Find all downloaded jpg files
    img_files = glob.glob(os.path.join(RAW_DIR, "*.jpg"))
    if not img_files:
        print("No images found in raw_images directory.")
        return

    print(f"Found {len(img_files)} candidate images. Extracting blendshapes...")
    print("=" * 60)

    for img_path in sorted(img_files):
        filename = os.path.basename(img_path)
        bgr_image = cv2.imread(img_path)
        if bgr_image is None:
            print(f"Failed to load: {filename}")
            continue
            
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        
        detection_result = detector.detect(mp_image)
        if not detection_result.face_blendshapes:
            print(f"File: {filename:<30} -> NO FACE DETECTED")
            print("-" * 60)
            continue
            
        blendshapes = detection_result.face_blendshapes[0]
        scores = {category.category_name: round(category.score, 4) for category in blendshapes}
        
        # Sort and filter active blendshapes (> 0.05)
        active = sorted({k: v for k, v in scores.items() if v > 0.05}.items(), key=lambda x: x[1], reverse=True)
        
        print(f"File: {filename:<30} -> FACE DETECTED!")
        print("Active blendshapes:")
        for shape, val in active[:15]:
            print(f"  {shape:<25}: {val}")
        print("-" * 60)

if __name__ == "__main__":
    inspect()

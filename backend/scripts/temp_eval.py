import urllib.request
import cv2
import os
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

ids = [
    'photo-1601412436009-d964bd02edbc',
    'photo-1542206395-9feb3edaa68d',
    'photo-1554151228-14d9def656e4',
    'photo-1503023345310-bd7c1de61c7d',
    'photo-1509460913899-515f1df34fea' # scowling man/woman
]
task_path = 'c:/Users/Dell/Downloads/VoiceAssistant/frontend/public/models/face_landmarker.task'

base_options = python.BaseOptions(model_asset_path=task_path)
options = vision.FaceLandmarkerOptions(base_options=base_options, output_face_blendshapes=True, num_faces=1)
detector = vision.FaceLandmarker.create_from_options(options)

for pid in ids:
    url = f'https://images.unsplash.com/{pid}?auto=format&fit=crop&w=500&q=80'
    path = f'test_{pid}.jpg'
    try:
        urllib.request.urlretrieve(url, path)
        bgr_image = cv2.imread(path)
        if bgr_image is None:
            print(f'ID: {pid} -> FAILED TO LOAD IMAGE')
            continue
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        result = detector.detect(mp_image)
        if result.face_blendshapes:
            scores = {c.category_name: c.score for c in result.face_blendshapes[0]}
            print(f'ID: {pid} -> FACE DETECTED!')
            print(f'  browDownLeft: {scores.get("browDownLeft", 0):.4f}, browDownRight: {scores.get("browDownRight", 0):.4f}')
            print(f'  mouthSmileLeft: {scores.get("mouthSmileLeft", 0):.4f}, mouthSmileRight: {scores.get("mouthSmileRight", 0):.4f}')
            print(f'  mouthFrownLeft: {scores.get("mouthFrownLeft", 0):.4f}, mouthFrownRight: {scores.get("mouthFrownRight", 0):.4f}')
        else:
            print(f'ID: {pid} -> NO FACE DETECTED')
    except Exception as e:
        print(f'ID: {pid} -> Error: {e}')

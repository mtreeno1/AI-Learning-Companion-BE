import numpy as np
from ultralytics import YOLO

class PoseEstimator:
    def __init__(self, model_path="models/yolov8n-pose.pt"):
        self.model = YOLO(model_path)

    def estimate(self, frame):
        results = self.model(frame, verbose=False)

        if (
            not results
            or results[0].keypoints is None
            or len(results[0].keypoints.xy) == 0
        ):
            return None

        kpts = results[0].keypoints.xy[0].cpu().numpy()

        nose = kpts[0]
        left_eye = kpts[1]
        right_eye = kpts[2]
        eye_center = (left_eye + right_eye) / 2

        yaw = np.degrees(np.arctan2(nose[0] - eye_center[0], 100))
        pitch = np.degrees(np.arctan2(nose[1] - eye_center[1], 100))

        return {
            "yaw": yaw,
            "pitch": pitch,
            "keypoints": kpts,
        }

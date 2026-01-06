"""
Pose estimation utilities
"""

import numpy as np
import cv2
from typing import Tuple, Optional


def draw_keypoints(frame: np.ndarray, keypoints: np.ndarray, color=(0, 255, 0)):
    """
    Vẽ keypoints lên frame
    """
    for x, y in keypoints: 
        if x > 0 and y > 0:
            cv2.circle(frame, (int(x), int(y)), 3, color, -1)


def draw_head_direction(
    frame: np.ndarray,
    keypoints: np.ndarray,
    yaw: float,
    pitch:  float
):
    """
    Vẽ hướng nhìn của đầu
    """
    try:
        nose = keypoints[0]
        if nose[0] == 0:
            return
        
        # Calculate arrow endpoint
        length = 100
        end_x = int(nose[0] + length * np.sin(np.radians(yaw)))
        end_y = int(nose[1] + length * np.sin(np.radians(pitch)))
        
        cv2.arrowedLine(
            frame,
            (int(nose[0]), int(nose[1])),
            (end_x, end_y),
            (255, 255, 0),
            2
        )
    except:
        pass


def get_face_bbox(keypoints: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """
    Tính bounding box của khuôn mặt từ keypoints
    
    Returns:
        (x1, y1, x2, y2) or None
    """
    try: 
        # Take face keypoints (0-4:  nose, eyes, ears)
        face_kpts = keypoints[: 5]
        valid_kpts = face_kpts[face_kpts[:, 0] > 0]
        
        if len(valid_kpts) == 0:
            return None
        
        x1 = int(valid_kpts[: , 0].min())
        y1 = int(valid_kpts[:, 1].min())
        x2 = int(valid_kpts[:, 0].max())
        y2 = int(valid_kpts[:, 1].max())
        
        # Add padding
        padding = 20
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 += padding
        y2 += padding
        
        return x1, y1, x2, y2
    except:
        return None
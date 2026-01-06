"""
Event Detection System - Simplified Version
Chỉ phát hiện:  Phone & Left Seat
"""

import numpy as np
import cv2
import time
from typing import Dict
from config.constants import *


class EventDetector:
    """
    Phát hiện các event ảnh hưởng đến tập trung
    - Phone detected
    - Left seat
    """
    
    def __init__(self):
        self.no_face_start = None
        
    def detect_events(
        self,
        frame: np. ndarray,
        det_results,
        pose_results,
        det_model,
        pose_model
    ) -> Dict[str, bool]:
        """
        Phát hiện events trong 1 frame
        
        Returns:
            {
                'phone_detected': bool,
                'left_seat': bool
            }
        """
        events = {
            'phone_detected': False,
            'left_seat': False
        }
        
        # 1. Phone Detection
        events['phone_detected'] = self._detect_phone(det_results, det_model)
        
        # 2. Person Detection (để xác định left seat)
        person_detected = self._detect_person(pose_results)
        
        if person_detected:
            # Có người → reset timer
            self.no_face_start = None
            events['left_seat'] = False
        else:
            # Không có người → check left seat
            events['left_seat'] = self._check_left_seat()
        
        return events
    
    def _detect_phone(self, det_results, det_model) -> bool:
        """
        Phát hiện điện thoại
        """
        try:
            if det_results is None: 
                return False
            
            for r in det_results: 
                if hasattr(r, 'boxes') and r.boxes is not None:
                    for box in r.boxes:
                        try:
                            cls_id = int(box.cls[0])
                            label = det_model.names[cls_id]
                            conf = float(box.conf[0])
                            
                            if label == "cell phone" and conf >= PHONE_CONFIDENCE_THRESHOLD:
                                return True
                        except (IndexError, KeyError, TypeError):
                            continue
        except Exception:
            pass
        
        return False
    
    def _detect_person(self, pose_results) -> bool:
        """
        Phát hiện có người trong frame hay không
        
        Returns:
            True nếu phát hiện được người
        """
        try:
            if pose_results is None or len(pose_results) == 0:
                return False
            
            # Check if keypoints exist
            if not hasattr(pose_results[0], 'keypoints'):
                return False
            
            if pose_results[0].keypoints is None:
                return False
            
            # Check if xy tensor exists and has data
            if not hasattr(pose_results[0].keypoints, 'xy'):
                return False
            
            xy_data = pose_results[0].keypoints.xy
            
            if xy_data is None or len(xy_data) == 0:
                return False
            
            # Get keypoints
            kpts = xy_data[0]. cpu().numpy()
            
            if len(kpts) == 0:
                return False
            
            # Check if at least one keypoint is visible (not [0, 0])
            # Nose (index 0) is usually most reliable
            if kpts. shape[0] > 0 and kpts[0][0] > 0 and kpts[0][1] > 0:
                return True
            
            # Fallback: check if any keypoint is visible
            visible_kpts = np.sum((kpts[: , 0] > 0) & (kpts[:, 1] > 0))
            return visible_kpts >= 3  # Ít nhất 3 keypoints visible
            
        except Exception:
            return False
    
    def _check_left_seat(self) -> bool:
        """
        Kiểm tra rời khỏi chỗ ngồi
        (không thấy người > FACE_MISSING_TIMEOUT)
        
        Returns:
            True nếu rời chỗ ngồi
        """
        try:
            current_time = time.time()
            
            if self.no_face_start is None:
                # Bắt đầu đếm thời gian không thấy người
                self. no_face_start = current_time
                return False
            
            # Tính thời gian không thấy người
            duration = current_time - self.no_face_start
            
            # Nếu > threshold → coi như rời chỗ ngồi
            return duration >= FACE_MISSING_TIMEOUT
            
        except Exception:
            return False
    
    def reset(self):
        """Reset trạng thái detector"""
        self.no_face_start = None
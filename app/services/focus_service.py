"""
Focus Detection Service - YOLO-based real-time focus tracking
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
import threading


class FocusDetectionService: 
    """
    AI Service for detecting focus/distraction using YOLO
    """
    def __init__(self, model_path: str = "yolov8n.pt"):
        """
        Initialize YOLO model
        
        Args:
            model_path: Path to YOLO model weights
        """
        print(f"🤖 Loading YOLO model:  {model_path}")
        self.model = YOLO(model_path)
        print("✅ YOLO model loaded successfully")
        
        # Alert management
        self.last_alert_time = None
        self.alert_cooldown = 3  # seconds between alerts
        
        # Detection thresholds
        self. PERSON_CONFIDENCE_THRESHOLD = 0.3
        self.PHONE_CONFIDENCE_THRESHOLD = 0.4
        self.NO_PERSON_TIMEOUT = 5  # seconds before "no person" alert
        
        # State tracking
        self.no_person_start_time = None
        self. consecutive_phone_detections = 0
        self.phone_detection_threshold = 3  # frames before alert
        
    def detect_frame(self, frame: np.ndarray) -> Dict: 
        """
        Detect objects in a single frame and determine focus status
        
        Args:
            frame: OpenCV image (BGR format)
            
        Returns: 
            {
                "is_focused": bool,           # Overall focus status
                "confidence": float,          # Detection confidence (0-1)
                "message": str,               # Human-readable status
                "alert_type": str|None,       # "warning", "danger", None
                "detections": [               # List of detected objects
                    {
                        "class": str,
                        "confidence": float,
                        "bbox": [x1, y1, x2, y2]
                    }
                ],
                "metrics": {
                    "person_detected": bool,
                    "phone_detected": bool,
                    "person_confidence": float,
                    "phone_confidence": float
                }
            }
        """
        # Run YOLO detection
        results = self.model(frame, verbose=False)
        
        # Parse detections
        person_detected = False
        phone_detected = False
        max_person_confidence = 0.0
        max_phone_confidence = 0.0
        detections = []
        
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = self.model.names[class_id]
                bbox = box.xyxy[0].tolist()
                
                detections.append({
                    "class": class_name,
                    "confidence": confidence,
                    "bbox": bbox
                })
                
                # Check for person
                if class_name == "person" and confidence > self.PERSON_CONFIDENCE_THRESHOLD:
                    person_detected = True
                    max_person_confidence = max(max_person_confidence, confidence)
                
                # Check for phone
                elif class_name == "cell phone" and confidence > self.PHONE_CONFIDENCE_THRESHOLD: 
                    phone_detected = True
                    max_phone_confidence = max(max_phone_confidence, confidence)
        
        # Determine focus status
        result = self._determine_focus_status(
            person_detected, 
            phone_detected,
            max_person_confidence,
            max_phone_confidence,
            detections
        )
        
        return result
    
    def _determine_focus_status(
        self, 
        person_detected: bool,
        phone_detected: bool,
        person_confidence: float,
        phone_confidence: float,
        detections: list
    ) -> Dict:
        """
        Determine focus status based on detections
        """
        current_time = datetime.now()
        
        # Priority 1: No person detected
        if not person_detected:
            if self.no_person_start_time is None:
                self. no_person_start_time = current_time
            
            elapsed = (current_time - self.no_person_start_time).total_seconds()
            
            if elapsed > self.NO_PERSON_TIMEOUT:
                return {
                    "is_focused": False,
                    "confidence": 0.0,
                    "message": "⚠️ No person detected - Are you still there?",
                    "alert_type": "warning",
                    "detections":  detections,
                    "metrics": {
                        "person_detected": False,
                        "phone_detected": False,
                        "person_confidence": 0.0,
                        "phone_confidence":  0.0,
                        "no_person_duration": elapsed
                    }
                }
            else:
                # Grace period - still searching
                return {
                    "is_focused": True,
                    "confidence": 0.3,
                    "message": "🔍 Searching for person...",
                    "alert_type": None,
                    "detections":  detections,
                    "metrics": {
                        "person_detected": False,
                        "phone_detected": False,
                        "person_confidence": 0.0,
                        "phone_confidence": 0.0
                    }
                }
        else:
            # Reset no-person timer
            self.no_person_start_time = None
        
        # Priority 2: Phone detected
        if phone_detected: 
            self.consecutive_phone_detections += 1
            
            if self.consecutive_phone_detections >= self.phone_detection_threshold:
                # Check alert cooldown
                should_alert = self._should_trigger_alert()
                
                return {
                    "is_focused": False,
                    "confidence": person_confidence,
                    "message": "📱 Phone detected - Stay focused!",
                    "alert_type": "danger" if should_alert else None,
                    "detections":  detections,
                    "metrics": {
                        "person_detected": True,
                        "phone_detected": True,
                        "person_confidence": person_confidence,
                        "phone_confidence": phone_confidence,
                        "consecutive_phone_frames": self.consecutive_phone_detections
                    }
                }
        else:
            # Reset phone detection counter
            self.consecutive_phone_detections = 0
        
        # Default:  Focused
        return {
            "is_focused": True,
            "confidence": person_confidence,
            "message": "✅ Focused - Great job!",
            "alert_type": None,
            "detections": detections,
            "metrics": {
                "person_detected": True,
                "phone_detected":  False,
                "person_confidence":  person_confidence,
                "phone_confidence": 0.0
            }
        }
    
    def _should_trigger_alert(self) -> bool:
        """
        Check if enough time has passed since last alert (cooldown)
        """
        current_time = datetime.now()
        
        if self.last_alert_time is None:
            self.last_alert_time = current_time
            return True
        
        elapsed = (current_time - self.last_alert_time).total_seconds()
        
        if elapsed >= self.alert_cooldown:
            self.last_alert_time = current_time
            return True
        
        return False
    
    def process_webcam_frame(self, frame_data: bytes) -> Tuple[Dict, np.ndarray]:
        """
        Process webcam frame from base64 or raw bytes
        
        Args:
            frame_data: Raw image bytes (JPEG/PNG)
            
        Returns: 
            (detection_result, annotated_frame)
        """
        # Decode frame
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise ValueError("Failed to decode frame")
        
        # Run detection
        result = self.detect_frame(frame)
        
        # Annotate frame with bounding boxes
        annotated_frame = self._annotate_frame(frame, result)
        
        return result, annotated_frame
    
    def _annotate_frame(self, frame: np. ndarray, result: Dict) -> np.ndarray:
        """
        Draw bounding boxes and status on frame
        """
        annotated = frame.copy()
        
        # Draw detections
        for det in result["detections"]:
            bbox = det["bbox"]
            x1, y1, x2, y2 = map(int, bbox)
            
            # Color based on class
            if det["class"] == "person": 
                color = (0, 255, 0)  # Green
            elif det["class"] == "cell phone":
                color = (0, 0, 255)  # Red
            else: 
                color = (255, 255, 0)  # Cyan
            
            # Draw box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{det['class']} {det['confidence']:.2f}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated, (x1, y1 - h - 10), (x1 + w, y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Draw status text
        status_color = (0, 255, 0) if result["is_focused"] else (0, 0, 255)
        status_text = result["message"]
        
        # Background for text
        (w, h), _ = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        cv2.rectangle(annotated, (10, 10), (w + 20, h + 30), (0, 0, 0), -1)
        cv2.putText(annotated, status_text, (15, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        
        # Draw confidence
        conf_text = f"Confidence: {result['confidence']:.2f}"
        cv2.putText(annotated, conf_text, (15, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return annotated
    
    def get_model_info(self) -> Dict:
        """
        Get information about loaded model
        """
        return {
            "model_type": "YOLOv8",
            "classes": list(self.model.names.values()),
            "num_classes": len(self.model.names),
            "focus_classes": ["person", "cell phone"],
            "thresholds": {
                "person_confidence": self.PERSON_CONFIDENCE_THRESHOLD,
                "phone_confidence": self.PHONE_CONFIDENCE_THRESHOLD,
                "alert_cooldown": self.alert_cooldown,
                "no_person_timeout": self.NO_PERSON_TIMEOUT
            }
        }


# Global singleton instance
_focus_service_instance = None

def get_focus_service() -> FocusDetectionService: 
    """
    Get or create global FocusDetectionService instance
    """
    global _focus_service_instance
    
    if _focus_service_instance is None:
        _focus_service_instance = FocusDetectionService()
    
    return _focus_service_instance
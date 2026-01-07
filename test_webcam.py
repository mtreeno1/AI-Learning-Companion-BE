"""
Real-time Focus Tracking với webcam
"""

from ultralytics import YOLO
import cv2
import time

from core.focus_scorer import FocusScorer
from core.event_detector import EventDetector
from core.alert_manager import AlertManager
from utils.pose_utils import draw_keypoints, draw_head_direction, get_face_bbox


def main():
    # Load models
    print("Loading models...")
    det = YOLO("models/yolov8n.pt")
    pose = YOLO("models/yolov8n-pose.pt")
    
    # Initialize systems
    scorer = FocusScorer()
    detector = EventDetector()
    alert_manager = AlertManager()
    
    # Start webcam
    cap = cv2.VideoCapture(0)
    
    print("Starting focus tracking... Press 'q' to quit, 'r' to reset score")
    
    while True: 
        ret, frame = cap.read()
        if not ret: 
            break
        
        # Run detection
        det_results = det(frame, conf=0.5, verbose=False)
        pose_results = pose(frame, verbose=False)
        
        # Detect events
        events = detector.detect_events(
            frame, det_results, pose_results, det, pose
        )
        
        # Update focus score
        focus_score = scorer.update(events)
        level, color = scorer.get_focus_level()
        
        # Check for alerts
        distraction_duration = scorer.get_distraction_duration()
        if alert_manager.should_alert(focus_score, distraction_duration):
            message = alert_manager.get_alert_message(focus_score, level)
            print(f"\n🔔 {message}\n")
            alert_manager.play_alert_sound(level)
        
        # ========== VISUALIZATION ==========
        
        # Draw phone detection
        if events['phone_detected']:
            for r in det_results:
                for box in r.boxes:
                    if det.names[int(box.cls[0])] == "cell phone":
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, "PHONE!", (x1, y1-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Draw pose
        if pose_results and pose_results[0].keypoints is not None:
            kpts = pose_results[0].keypoints.xy[0].cpu().numpy()
            if len(kpts) > 0:
                draw_keypoints(frame, kpts)
                
                # Calculate head pose for visualization
                from core.event_detector import EventDetector
                temp_detector = EventDetector()
                yaw, pitch = temp_detector._calculate_head_pose(kpts)
                if yaw is not None: 
                    draw_head_direction(frame, kpts, yaw, pitch)
                    cv2.putText(frame, f"Yaw: {yaw:.1f} Pitch: {pitch:.1f}",
                                (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Draw focus score (BIG)
        score_color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (4, 2, 0))  # BGR
        cv2.putText(frame, f"FOCUS: {focus_score:.1f}", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, score_color, 3)
        
        # Draw level
        cv2.putText(frame, level.upper().replace('_', ' '), (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, score_color, 2)
        
        # Draw active events
        y_offset = 140
        for event_name, is_active in events.items():
            if is_active:
                cv2.putText(frame, f"⚠ {event_name}", (20, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                y_offset += 25
        
        # Draw distraction timer
        if distraction_duration: 
            cv2.putText(frame, f"Distracted:  {distraction_duration:.1f}s", (20, frame.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        
        cv2.imshow("AI Learning Companion", frame)
        
        # Keyboard control
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            scorer.reset()
            print("\n✅ Score reset to 100\n")
    
    # Session summary
    stats = scorer.get_session_stats()
    print("\n" + "="*50)
    print("SESSION SUMMARY")
    print("="*50)
    for key, value in stats.items():
        print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
    print("="*50)
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
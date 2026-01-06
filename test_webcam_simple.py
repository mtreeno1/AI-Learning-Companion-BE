"""
Simple Webcam Test - Test focus tracking trực tiếp qua camera
Chỉ phát hiện:  Phone & Left Seat

Phím tắt: 
- 'q':  Thoát
- 'r':  Reset điểm về 100
- 's': Hiển thị thống kê hiện tại
"""

from ultralytics import YOLO
import cv2
import time

from core.focus_scorer import FocusScorer
from core.event_detector import EventDetector
from core. alert_manager import AlertManager


def draw_ui(frame, focus_score, level, color, events, distraction_duration):
    """
    Vẽ UI lên frame - Chỉ hiển thị Phone & Left Seat
    """
    h, w = frame.shape[:2]
    
    # Convert hex color to BGR
    try:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        bgr_color = (b, g, r)
    except:
        bgr_color = (0, 255, 0)
    
    # 1. Draw focus score (BIG, center-top)
    score_text = f"{focus_score:.1f}"
    cv2.putText(frame, score_text, (w//2 - 80, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 2.5, bgr_color, 4)
    
    # 2. Draw level below score
    level_text = level. upper().replace('_', ' ')
    cv2.putText(frame, level_text, (w//2 - 100, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, bgr_color, 2)
    
    # 3. Draw progress bar
    bar_width = 300
    bar_height = 20
    bar_x = (w - bar_width) // 2
    bar_y = 130
    
    # Background
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                  (50, 50, 50), -1)
    
    # Fill
    fill_width = int(bar_width * (focus_score / 100))
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height),
                  bgr_color, -1)
    
    # Border
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                  (255, 255, 255), 2)
    
    # 4. Draw active events (left side) - CHỈ PHONE & LEFT SEAT
    y_offset = 200
    cv2.putText(frame, "EVENTS:", (20, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    y_offset += 30
    
    # ✅ CHỈ 2 events
    event_icons = {
        'phone_detected': 'Phone Detected',
        'left_seat': 'Left Seat'
    }
    
    active_count = 0
    for event_name, label in event_icons.items():
        is_active = events.get(event_name, False)
        if is_active:
            # Draw red indicator
            cv2.circle(frame, (35, y_offset - 5), 8, (0, 0, 255), -1)
            cv2.putText(frame, label, (55, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            y_offset += 35
            active_count += 1
    
    if active_count == 0:
        # Green checkmark
        cv2.circle(frame, (35, y_offset - 5), 8, (0, 255, 0), -1)
        cv2.putText(frame, "All Good", (55, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # 5. Draw distraction timer (bottom center)
    if distraction_duration is not None and distraction_duration > 0:
        timer_text = f"Distracted:  {distraction_duration:.1f}s"
        timer_size = cv2.getTextSize(timer_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        timer_x = (w - timer_size[0]) // 2
        
        # Background rectangle
        padding = 10
        cv2.rectangle(frame, 
                     (timer_x - padding, h - 60 - padding),
                     (timer_x + timer_size[0] + padding, h - 60 + timer_size[1] + padding),
                     (0, 0, 0), -1)
        cv2.rectangle(frame,
                     (timer_x - padding, h - 60 - padding),
                     (timer_x + timer_size[0] + padding, h - 60 + timer_size[1] + padding),
                     (0, 165, 255), 2)
        
        cv2.putText(frame, timer_text, (timer_x, h - 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
    
    # 6. Draw controls (bottom-left)
    controls = "Q: Quit | R:Reset | S:Stats"
    cv2.putText(frame, controls, (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)


def main():
    print("=" * 60)
    print("🎓 AI Learning Companion - Focus Tracker")
    print("=" * 60)
    print("Loading models...")
    
    # Load YOLO models
    det = YOLO("models/yolov8n.pt")
    pose = YOLO("models/yolov8n-pose.pt")
    print("✅ Models loaded!")
    
    # Initialize systems
    scorer = FocusScorer()
    detector = EventDetector()
    alert_manager = AlertManager()
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    if not cap. isOpened():
        print("❌ Error: Could not open webcam")
        return
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("\n✅ Webcam opened successfully!")
    print("=" * 60)
    print("Detecting:")
    print("  📱 Phone Usage")
    print("  🚶 Left Seat")
    print("=" * 60)
    print("Controls:")
    print("  Q - Quit")
    print("  R - Reset score to 100")
    print("  S - Show current statistics")
    print("=" * 60)
    print("\nStarting focus tracking.. .\n")
    
    # FPS calculation
    fps_start_time = time.time()
    fps_counter = 0
    fps_display = 0
    
    # Initialize variables
    focus_score = 100.0
    level = 'highly_focused'
    color = '#00FF00'
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error: Could not read frame")
            break
        
        # Run detection
        det_results = det(frame, conf=0.5, verbose=False)
        pose_results = pose(frame, verbose=False)
        
        # Detect events (chỉ phone & left seat)
        events = detector. detect_events(
            frame, det_results, pose_results, det, pose
        )
        
        # Update focus score
        focus_score = scorer.update(events)
        level, color = scorer.get_focus_level()
        
        # Check for alerts
        distraction_duration = scorer.get_distraction_duration()
        if alert_manager.should_alert(focus_score, distraction_duration):
            message = alert_manager.get_alert_message(focus_score, level)
            print(f"\n🔔 {message}")
            alert_manager.play_alert_sound(level)
        
        # Draw UI
        draw_ui(frame, focus_score, level, color, events, distraction_duration)
        
        # Calculate FPS
        fps_counter += 1
        if time.time() - fps_start_time >= 1.0:
            fps_display = fps_counter
            fps_counter = 0
            fps_start_time = time. time()
        
        # Draw FPS (top right)
        cv2.putText(frame, f"FPS: {fps_display}", (frame.shape[1] - 100, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow("AI Learning Companion - Focus Tracker", frame)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\n👋 Quitting...")
            break
        
        elif key == ord('r'):
            scorer.reset()
            detector.reset()
            print("\n✅ Score reset to 100\n")
        
        elif key == ord('s'):
            stats = scorer.get_session_stats()
            print("\n" + "=" * 60)
            print("📊 CURRENT STATISTICS")
            print("=" * 60)
            print(f"Current Score:         {focus_score:.2f}")
            print(f"Current Level:         {level. replace('_', ' ').title()}")
            print(f"Average Score:         {stats.get('avg_score', 0):.2f}")
            print(f"Min Score:             {stats.get('min_score', 0):.2f}")
            print(f"Max Score:             {stats.get('max_score', 0):.2f}")
            print(f"Total Violations:      {stats.get('total_violations', 0)}")
            print(f"  - Phone Detected:     {stats.get('phone_detected_count', 0)}")
            print(f"  - Left Seat:         {stats.get('left_seat_count', 0)}")
            print(f"Duration:              {stats.get('duration_seconds', 0):.0f}s")
            print("=" * 60 + "\n")
    
    # Final summary
    stats = scorer.get_session_stats()
    
    if stats:
        print("\n" + "=" * 60)
        print("📊 FINAL SESSION SUMMARY")
        print("=" * 60)
        print(f"Final Score:            {focus_score:.2f}")
        print(f"Average Score:         {stats.get('avg_score', 0):.2f}")
        print(f"Min Score:             {stats.get('min_score', 0):.2f}")
        print(f"Max Score:             {stats.get('max_score', 0):.2f}")
        print(f"Total Violations:       {stats.get('total_violations', 0)}")
        print(f"  - Phone Detected:    {stats.get('phone_detected_count', 0)}")
        print(f"  - Left Seat:         {stats.get('left_seat_count', 0)}")
        print(f"Session Duration:      {stats.get('duration_seconds', 0):.0f}s ({stats.get('duration_seconds', 0)/60:.1f} minutes)")
        print("=" * 60)
    else:
        print("\n⚠️ No session data recorded")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Camera released.  Goodbye!  👋\n")


if __name__ == "__main__":
    main()
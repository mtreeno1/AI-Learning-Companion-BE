"""
Focus Scoring System - Simplified Version
Chỉ xử lý: Phone & Left Seat
"""

import time
from typing import Dict, Optional, Tuple
from config.constants import *
from utils.smoothing import ExponentialMovingAverage


class FocusScorer:
    """
    Quản lý điểm tập trung theo thời gian với penalty và recovery
    """
    
    def __init__(self):
        self.score = INITIAL_FOCUS_SCORE
        self.score_raw = INITIAL_FOCUS_SCORE
        self.ema = ExponentialMovingAverage(alpha=EMA_ALPHA)
        
        # Tracking state
        self.last_update_time = time.time()
        self.distraction_start_time = None
        self.last_violation_time = None
        
        # Event tracking (for time-based penalties)
        self.left_seat_start = None
        
        # History for analytics
        self.history = []
        
    def update(self, events: Dict[str, bool]) -> float:
        """
        Cập nhật điểm dựa trên các event hiện tại
        
        Args:
            events: {
                'phone_detected': bool,
                'left_seat':  bool
            }
            
        Returns:
            Current focus score (0-100)
        """
        current_time = time.time()
        delta_t = current_time - self.last_update_time
        
        # Calculate penalties
        total_penalty = 0.0
        
        # 1.Phone detected (discrete penalty)
        if events.get('phone_detected', False):
            total_penalty += PENALTY_PHONE_DETECTED
            self.last_violation_time = current_time
        
        # 2.Left seat (discrete penalty - chỉ áp dụng 1 lần khi mới rời)
        if events.get('left_seat', False):
            if self.left_seat_start is None:
                # Mới rời chỗ ngồi → trừ điểm
                total_penalty += PENALTY_LEFT_SEAT
                self.left_seat_start = current_time
            # Nếu đã rời từ trước → không trừ thêm
        else:
            # Quay lại chỗ ngồi → reset
            self.left_seat_start = None
        
        # 3.Recovery (nếu không có vi phạm)
        recovery = 0.0
        if total_penalty == 0 and not any(events.values()):
            recovery = min(RECOVERY_RATE_PER_SEC * delta_t, MAX_RECOVERY_PER_UPDATE)
        else:
            # Track distraction period
            if self.distraction_start_time is None:
                self.distraction_start_time = current_time
        
        # If no distraction, reset tracking
        if total_penalty == 0 and not any(events.values()):
            self.distraction_start_time = None
        
        # 4.Update raw score
        self.score_raw = max(0, min(100, self.score_raw - total_penalty + recovery))
        
        # 5.Apply EMA smoothing
        self.score = self.ema.update(self.score_raw)
        
        # 6.Save to history
        self.history.append({
            'timestamp': current_time,
            'score': self.score,
            'score_raw': self.score_raw,
            'penalty': total_penalty,
            'recovery': recovery,
            'events': events.copy()
        })
        
        self.last_update_time = current_time
        return self.score
    
    def get_focus_level(self) -> Tuple[str, str]:
        """
        Trả về level và màu sắc tương ứng
        
        Returns:
            (level_name, color)
        """
        for level, (min_score, max_score) in FOCUS_LEVELS.items():
            if min_score <= self.score <= max_score:
                colors = {
                    'highly_focused':  '#00FF00',
                    'focused':  '#90EE90',
                    'distracted': '#FFA500',
                    'severely_distracted': '#FF0000'
                }
                return level, colors[level]
        
        return 'unknown', '#FFFFFF'
    
    def get_distraction_duration(self) -> Optional[float]: 
        """
        Trả về thời gian mất tập trung liên tục (seconds)
        """
        if self.distraction_start_time is None:
            return None
        return time.time() - self.distraction_start_time
    
    def reset(self):
        """Reset về trạng thái ban đầu"""
        self.score = INITIAL_FOCUS_SCORE
        self.score_raw = INITIAL_FOCUS_SCORE
        self.ema.reset()
        self.last_update_time = time.time()
        self.distraction_start_time = None
        self.last_violation_time = None
        self.left_seat_start = None
        
    def get_session_stats(self) -> Dict:
        """
        Thống kê toàn session
        """
        if not self.history:
            return {}
        
        scores = [h['score'] for h in self.history]
        
        # Đếm số lần vi phạm từng loại
        phone_violations = sum(1 for h in self.history if h['events'].get('phone_detected', False))
        left_seat_violations = sum(1 for h in self.history if h['events'].get('left_seat', False))
        
        return {
            'avg_score': sum(scores) / len(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'final_score': self.score,
            'total_violations': sum(1 for h in self.history if any(h['events'].values())),
            'phone_detected_count': phone_violations,
            'left_seat_count': left_seat_violations,
            'duration_seconds': self.history[-1]['timestamp'] - self.history[0]['timestamp']
        }
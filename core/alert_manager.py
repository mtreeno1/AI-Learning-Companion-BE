"""
Smart Alert System - Cảnh báo thông minh với giọng nói AI
"""

import time
from typing import Optional
from config.constants import *
import os


class AlertManager:
    """
    Quản lý cảnh báo với cooldown và điều kiện kích hoạt
    """
    
    def __init__(self):
        self.last_alert_time = 0
        self.alert_pending = False
        self.alert_trigger_start = None
        
        # Initialize pygame mixer for sound
        self.sound_enabled = False
        self.sounds = {}
        self._init_sound()
        
    def _init_sound(self):
        """Initialize pygame mixer and load sounds"""
        try: 
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            
            # Load voice alert files (MP3 from Edge TTS)
            sound_files = {
                'distracted': 'assets/gentle_voice_alert.mp3',
                'severely_distracted': 'assets/urgent_voice_alert.mp3',
                'motivational': 'assets/motivational_voice.mp3'
            }
            
            for level, filepath in sound_files.items():
                if os.path.exists(filepath):
                    self.sounds[level] = pygame.mixer.Sound(filepath)
                    
                    # Set volume based on level
                    if level == 'severely_distracted':
                        self.sounds[level].set_volume(0.8)  # 80% volume
                    else:
                        self.sounds[level].set_volume(0.6)  # 60% volume
            
            if self.sounds:
                self.sound_enabled = True
                print(f"✅ Loaded {len(self.sounds)} voice alerts")
            else:
                print("⚠️ No voice alert files found.")
                print("   Run:  python generate_voice_alerts.py")
                
        except ImportError:
            print("⚠️ pygame not installed.Install with: pip install pygame")
        except Exception as e:
            print(f"⚠️ Failed to initialize sound: {str(e)}")
        
    def should_alert(
        self,
        focus_score: float,
        distraction_duration: Optional[float]
    ) -> bool:
        """
        Quyết định có nên cảnh báo không
        
        Điều kiện:
        1.Score < ALERT_SCORE_THRESHOLD
        2.Mất tập trung liên tục > ALERT_TRIGGER_DURATION
        3.Đã qua ALERT_COOLDOWN kể từ lần cảnh báo trước
        
        Returns:
            True nếu cần cảnh báo
        """
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_alert_time < ALERT_COOLDOWN:
            return False
        
        # Check score threshold
        if focus_score >= ALERT_SCORE_THRESHOLD:
            self.alert_trigger_start = None
            return False
        
        # Check distraction duration
        if distraction_duration is None:
            self.alert_trigger_start = None
            return False
        
        if distraction_duration >= ALERT_TRIGGER_DURATION:
            self.last_alert_time = current_time
            self.alert_trigger_start = None
            return True
        
        return False
    
    def get_alert_message(self, focus_score: float, level: str) -> str:
        """
        Tạo message cảnh báo phù hợp với mức độ
        """
        messages = {
            'distracted': f"⚠️ Bạn đang mất tập trung (Score: {focus_score:.0f})",
            'severely_distracted': f"🚨 Độ tập trung rất thấp!  (Score: {focus_score:.0f})"
        }
        
        return messages.get(level, f"Focus:  {focus_score:.0f}")
    
    def play_alert_sound(self, level: str):
        """
        Phát giọng nói AI nhắc nhở
        """
        if self.sound_enabled and level in self.sounds:
            try:
                # Stop any currently playing alert
                for sound in self.sounds.values():
                    sound.stop()
                
                # Play new alert
                self.sounds[level].play()
                print(f"🔊 Playing voice alert for level: {level}")
            except Exception as e:
                print(f"🔔 Failed to play sound: {str(e)}")
        else:
            print(f"🔔 Alert for level: {level} (voice not available)")
            if not self.sound_enabled:
                print("   Tip: Run 'python generate_voice_alerts.py' to generate voices")
    
    def play_motivational(self):
        """
        Phát lời động viên khi học tốt
        (Có thể gọi khi focus_score > 90 liên tục)
        """
        if self.sound_enabled and 'motivational' in self.sounds:
            try:
                self.sounds['motivational'].play()
                print("🎉 Playing motivational message")
            except Exception as e: 
                print(f"Failed to play motivational sound: {str(e)}")
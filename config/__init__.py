"""
Configuration package for AI Learning Companion
"""

from .constants import (
    # Score settings
    INITIAL_FOCUS_SCORE,
    
    # Penalties
    PENALTY_PHONE_DETECTED,
    PENALTY_LEFT_SEAT,
    PENALTY_FACE_MISSING_PER_SEC,
    MIN_DURATION_FOR_PENALTY,
    
    # Recovery
    RECOVERY_RATE_PER_SEC,
    MAX_RECOVERY_PER_UPDATE,
    
    # Detection thresholds
    PHONE_CONFIDENCE_THRESHOLD,
    FACE_MISSING_TIMEOUT,
    
    # Alert system
    ALERT_COOLDOWN,
    ALERT_TRIGGER_DURATION,
    ALERT_SCORE_THRESHOLD,
    
    # Smoothing
    EMA_ALPHA,
    
    # Focus levels
    FOCUS_LEVELS,
    
    # Tracking
    FPS,
)

__all__ = [
    'INITIAL_FOCUS_SCORE',
    'PENALTY_PHONE_DETECTED',
    'PENALTY_LEFT_SEAT',
    'PENALTY_FACE_MISSING_PER_SEC',
    'MIN_DURATION_FOR_PENALTY',
    'RECOVERY_RATE_PER_SEC',
    'MAX_RECOVERY_PER_UPDATE',
    'PHONE_CONFIDENCE_THRESHOLD',
    'FACE_MISSING_TIMEOUT',
    'ALERT_COOLDOWN',
    'ALERT_TRIGGER_DURATION',
    'ALERT_SCORE_THRESHOLD',
    'EMA_ALPHA',
    'FOCUS_LEVELS',
    'FPS',
]
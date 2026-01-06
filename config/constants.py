# """
# Configuration constants for Focus Scoring System
# """

# # ==================== INITIAL SCORE ====================
# INITIAL_FOCUS_SCORE = 100.0

# # ==================== EVENT PENALTIES (Discrete) ====================
# PENALTY_PHONE_DETECTED = 10.0
# PENALTY_FALL_ASLEEP = 10.0
# PENALTY_LEFT_SEAT = 10.0

# # ==================== TIME-BASED PENALTIES (per second) ====================
# PENALTY_FACE_MISSING_PER_SEC = 2.0
# PENALTY_HEAD_TURNED_PER_SEC = 1.5

# # Minimum duration before applying time-based penalty
# MIN_DURATION_FOR_PENALTY = 2.0  # seconds

# # ==================== RECOVERY ====================
# RECOVERY_RATE_PER_SEC = 0.5  # điểm/giây
# MAX_RECOVERY_PER_UPDATE = 10.0

# # ==================== DETECTION THRESHOLDS ====================
# # Head pose
# HEAD_YAW_THRESHOLD = 25.0  # degrees
# HEAD_PITCH_THRESHOLD = 20.0  # degrees

# # Fall asleep detection
# SLEEP_PITCH_THRESHOLD = 35.0  # degrees (cúi đầu)
# SLEEP_EYE_CLOSED_DURATION = 3.0  # seconds
# SLEEP_MOTION_THRESHOLD = 0.02  # very low motion

# # Phone detection confidence
# PHONE_CONFIDENCE_THRESHOLD = 0.5

# # Face detection
# FACE_MISSING_TIMEOUT = 2.0  # seconds

# # ==================== ALERT SYSTEM ====================
# ALERT_COOLDOWN = 10.0  # seconds - không cảnh báo liên tục
# ALERT_TRIGGER_DURATION = 5.0  # seconds - mất tập trung > 5s mới báo
# ALERT_SCORE_THRESHOLD = 65.0  # dưới 65 điểm mới cảnh báo

# # ==================== EMA SMOOTHING ====================
# EMA_ALPHA = 0.3  # smoothing factor (0-1, càng nhỏ càng mượt)

# # ==================== FOCUS LEVELS ====================
# FOCUS_LEVELS = {
#     "highly_focused": (85, 100),
#     "focused": (65, 84),
#     "distracted": (40, 64),
#     "severely_distracted": (0, 39)
# }

# # ==================== TRACKING ====================
# FPS = 30  # frames per second for video processing


# v2

"""
Configuration constants for Focus Scoring System
"""

# ==================== INITIAL SCORE ====================
INITIAL_FOCUS_SCORE = 100.0

# ==================== EVENT PENALTIES (Discrete) ====================
PENALTY_PHONE_DETECTED = 5.0
PENALTY_LEFT_SEAT = 5.0

# ==================== TIME-BASED PENALTIES (per second) ====================
PENALTY_FACE_MISSING_PER_SEC = 2.0

# Minimum duration before applying time-based penalty
MIN_DURATION_FOR_PENALTY = 2.0  # seconds

# ==================== RECOVERY ====================
RECOVERY_RATE_PER_SEC = 0.5  # điểm/giây
MAX_RECOVERY_PER_UPDATE = 10.0

# ==================== DETECTION THRESHOLDS ====================
# Phone detection confidence
PHONE_CONFIDENCE_THRESHOLD = 0.5

# Face detection timeout (để xác định left seat)
FACE_MISSING_TIMEOUT = 1.0  # seconds - không thấy mặt > 3s = rời chỗ ngồi

# ==================== ALERT SYSTEM ====================
ALERT_COOLDOWN = 5.0  # seconds - không cảnh báo liên tục
ALERT_TRIGGER_DURATION = 5.0  # seconds - mất tập trung > 5s mới báo
ALERT_SCORE_THRESHOLD = 65.0  # dưới 65 điểm mới cảnh báo

# ==================== EMA SMOOTHING ====================
EMA_ALPHA = 0.3  # smoothing factor (0-1, càng nhỏ càng mượt)

# ==================== FOCUS LEVELS ====================
FOCUS_LEVELS = {
    "highly_focused": (85, 100),
    "focused": (65, 84),
    "distracted": (40, 64),
    "severely_distracted": (0, 39)
}

# ==================== TRACKING ====================
FPS = 30  # frames per second for video processing
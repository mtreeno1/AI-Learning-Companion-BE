class FocusLogic:
    def __init__(self, yaw_thresh=25, pitch_thresh=20):
        self.yaw_thresh = yaw_thresh
        self.pitch_thresh = pitch_thresh

    def evaluate(self, phone_detected, pose):
        if phone_detected:
            return False, "Phone detected"

        if pose is None:
            return False, "No face detected"

        if abs(pose["yaw"]) > self.yaw_thresh:
            return False, "Head turned"

        if abs(pose["pitch"]) > self.pitch_thresh:
            return False, "Looking down/up"

        return True, "Focused"

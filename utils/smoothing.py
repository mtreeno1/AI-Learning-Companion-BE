"""
Smoothing utilities - EMA filter
"""


class ExponentialMovingAverage: 
    """
    Exponential Moving Average for smooth score transitions
    """
    
    def __init__(self, alpha: float = 0.3):
        """
        Args:
            alpha: smoothing factor (0-1)
                   càng nhỏ càng mượt, càng lớn càng nhanh phản ứng
        """
        self.alpha = alpha
        self.value = None
        
    def update(self, new_value: float) -> float:
        """
        Update EMA với giá trị mới
        """
        if self.value is None:
            self.value = new_value
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        
        return self.value
    
    def reset(self):
        """Reset EMA"""
        self.value = None
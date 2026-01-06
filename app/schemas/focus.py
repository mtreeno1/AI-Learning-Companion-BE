from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class SessionCreate(BaseModel):
    """Schema for creating a new learning session"""
    session_name: str = Field(..., min_length=1, max_length=255, description="Name of the session")
    subject: str = Field(..., min_length=1, max_length=100, description="Subject being studied")
    initial_score: float = Field(default=100.0, ge=0, le=100, description="Initial score")


class SessionUpdate(BaseModel):
    """Schema for updating session data"""
    status: str = Field(..., description="Session status (active, completed, cancelled)")


class SessionStats(BaseModel):
    """Real-time session statistics"""
    session_id: UUID
    duration_seconds: int
    current_score: float
    total_violations: int
    phone_detected_count: int
    left_seat_count: int
    total_alerts: int
    gentle_alerts: int
    urgent_alerts: int
    focus_percentage: float
    total_frames: Optional[int] = 0
    focused_frames: Optional[int] = 0

    class Config:
        from_attributes = True


class DetectionResult(BaseModel):
    """AI detection result for a single frame"""
    session_id:  UUID
    timestamp: datetime
    is_focused:  bool
    person_detected: bool
    phone_detected: bool
    confidence: float
    message: str
    alert_type: Optional[str] = None
    stats: SessionStats


class SessionResponse(BaseModel):
    """Response schema for session data"""
    session_id: UUID
    user_id: UUID
    session_name: Optional[str]
    subject: Optional[str]
    
    # Timestamps
    started_at:  datetime
    ended_at: Optional[datetime] = None
    created_at:  datetime
    updated_at: Optional[datetime] = None
    
    # Duration
    duration_seconds: Optional[int] = 0
    
    # Scores
    initial_score: float
    current_score: float
    final_score: Optional[float] = None
    average_score: Optional[float] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    
    # Violations
    total_violations: int
    phone_detected_count: int
    left_seat_count:  int
    
    # Alerts
    total_alerts: int
    gentle_alerts: int
    urgent_alerts:  int
    
    # Focus metrics
    focus_percentage: float

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Response schema for listing sessions"""
    sessions: list[SessionResponse]
    total: int
    page: int
    page_size:  int
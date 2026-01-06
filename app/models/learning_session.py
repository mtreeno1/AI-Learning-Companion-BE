from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base
from decimal import Decimal


class LearningSession(Base):
    __tablename__ = "learning_sessions"
    
    # Primary Key
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session Info
    session_name = Column(String(255), nullable=True)
    subject = Column(String(100), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True))
    
    duration_seconds = Column(Integer, nullable=True)
    
    # Scores
    initial_score = Column(Float, default=100.0)
    current_score = Column(Float, default=100.0)
    final_score = Column(Float)
    average_score = Column(Float)
    min_score = Column(Float)
    max_score = Column(Float)
    
    # Violations
    total_violations = Column(Integer, default=0)
    phone_detected_count = Column(Integer, default=0)
    left_seat_count = Column(Integer, default=0)
    
    # Alerts
    total_alerts = Column(Integer, default=0)
    gentle_alerts = Column(Integer, default=0)
    urgent_alerts = Column(Integer, default=0)
    
 # Counters
    total_violations = Column(Integer, default=0)
    phone_detected_count = Column(Integer, default=0)
    left_seat_count = Column(Integer, default=0)
    total_alerts = Column(Integer, default=0)
    gentle_alerts = Column(Integer, default=0)
    urgent_alerts = Column(Integer, default=0)
    
    # Focus metrics
    focus_percentage = Column(Float, default=100.0)
    
    # Relationships
    video_recordings = relationship("VideoRecording", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LearningSession {self.session_id} - {self.session_name}>"
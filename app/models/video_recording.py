"""
Video Recording Model - Database model for video recordings
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.database import Base


class VideoRecording(Base):
    """
    Model for storing video recording metadata
    """
    __tablename__ = "video_recordings"
    
    # Primary key
    recording_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to learning session
    session_id = Column(UUID(as_uuid=True), ForeignKey("learning_sessions.session_id"), nullable=False, index=True)
    
    # File information
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    file_size_bytes = Column(Integer, default=0)
    
    # Recording metadata
    fps = Column(Float, default=30.0)
    resolution_width = Column(Integer, default=1920)
    resolution_height = Column(Integer, default=1080)
    codec = Column(String, default="mp4v")
    duration_seconds = Column(Float, default=0.0)
    frame_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Cloud storage (optional)
    cloud_storage_url = Column(String, nullable=True)
    cloud_storage_provider = Column(String, nullable=True)  # 's3', 'azure', 'gcs'
    
    # Relationship to learning session
    session = relationship("LearningSession", back_populates="video_recordings")
    
    def __repr__(self):
        return f"<VideoRecording {self.recording_id} session={self.session_id} file={self.filename}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'recording_id': str(self.recording_id),
            'session_id': str(self.session_id),
            'filename': self.filename,
            'filepath': self.filepath,
            'file_size_bytes': self.file_size_bytes,
            'file_size_mb': round(self.file_size_bytes / (1024 * 1024), 2) if self.file_size_bytes else 0,
            'fps': self.fps,
            'resolution': f"{self.resolution_width}x{self.resolution_height}",
            'resolution_width': self.resolution_width,
            'resolution_height': self.resolution_height,
            'codec': self.codec,
            'duration_seconds': self.duration_seconds,
            'frame_count': self.frame_count,
            'is_active': self.is_active,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'cloud_storage_url': self.cloud_storage_url,
            'cloud_storage_provider': self.cloud_storage_provider,
        }

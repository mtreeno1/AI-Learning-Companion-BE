"""
Video Recording Service - Server-side video recording for AI Learning Companion

This service handles real-time video recording on the backend to avoid overloading 
the browser.It records high-quality video while streaming lightweight snapshots 
to the frontend.

Features:
- Record high-quality video (Full HD, configurable FPS)
- Save videos to local disk or cloud storage
- Minimal browser overhead (metadata + snapshots only)
- Configurable recording parameters
"""

import cv2
import numpy as np
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class VideoRecordingService:
    """
    Service for recording video frames on the backend while performing AI detection.
    Allows high-quality recording without overloading the browser.
    """
    
    def __init__(self, storage_path: str = "recordings"):
        """
        Initialize the video recording service.
        
        Args:
            storage_path: Base directory for storing recorded videos
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Recording state
        self.recordings: Dict[str, Dict] = {}  # session_id -> recording info
        self.lock = threading.Lock()
        
        # Default recording configuration
        self.default_config = {
            'fps': 30.0,  # High FPS for quality recording
            'resolution': (1920, 1080),  # Full HD
            'codec': 'mp4v',  # H.264 compatible codec
            'quality': 95,  # High quality (0-100)
        }
        
        logger.info(f"Video recording service initialized.Storage: {self.storage_path}")
    
    def start_recording(
        self, 
        session_id: str,
        fps: Optional[float] = None,
        resolution: Optional[Tuple[int, int]] = None,
        codec: Optional[str] = None
    ) -> Dict:
        """
        Start recording video for a session.
        
        Args:
            session_id: Unique session identifier
            fps: Frames per second for recording (default: 30)
            resolution: Video resolution (width, height) (default: 1920x1080)
            codec: Video codec fourcc code (default: 'mp4v')
            
        Returns:
            Recording info dictionary
        """
        with self.lock:
            if session_id in self.recordings:
                logger.warning(f"Recording already active for session {session_id}")
                return self.recordings[session_id]
            
            # Use provided config or defaults
            fps = fps or self.default_config['fps']
            resolution = resolution or self.default_config['resolution']
            codec = codec or self.default_config['codec']
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{session_id}_{timestamp}.mp4"
            filepath = self.storage_path / filename
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = cv2.VideoWriter(
                str(filepath),
                fourcc,
                fps,
                resolution
            )
            
            if not writer.isOpened():
                logger.error(f"Failed to open video writer for {filepath}")
                raise RuntimeError("Failed to initialize video writer")
            
            # Store recording info
            recording_info = {
                'session_id': session_id,
                'filepath': str(filepath),
                'filename': filename,
                'writer': writer,
                'fps': fps,
                'resolution': resolution,
                'codec': codec,
                'started_at': datetime.now(),
                'frame_count': 0,
                'is_recording': True,
            }
            
            self.recordings[session_id] = recording_info
            
            logger.info(f"Started recording for session {session_id}")
            logger.info(f"  File: {filename}")
            logger.info(f"  Resolution: {resolution[0]}x{resolution[1]}")
            logger.info(f"  FPS: {fps}")
            
            return {
                'session_id': session_id,
                'filename': filename,
                'filepath': str(filepath),
                'fps': fps,
                'resolution': resolution,
                'started_at': recording_info['started_at'].isoformat(),
            }
    
    def write_frame(self, session_id: str, frame: np.ndarray) -> bool:
        """
        Write a frame to the recording.
        
        Args:
            session_id: Session identifier
            frame: Video frame (numpy array in BGR format)
            
        Returns:
            True if frame was written successfully, False otherwise
        """
        with self.lock:
            if session_id not in self.recordings:
                return False
            
            recording = self.recordings[session_id]
            
            if not recording['is_recording']:
                return False
            
            writer = recording['writer']
            target_resolution = recording['resolution']
            
            # Resize frame if necessary
            if frame.shape[1] != target_resolution[0] or frame.shape[0] != target_resolution[1]:
                frame = cv2.resize(frame, target_resolution)
            
            # Write frame
            try:
                writer.write(frame)
                recording['frame_count'] += 1
                return True
            except Exception as e:
                logger.error(f"Error writing frame for session {session_id}: {e}")
                return False
    
    def stop_recording(self, session_id: str) -> Optional[Dict]:
        """
        Stop recording for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Final recording info or None if session not found
        """
        with self.lock:
            if session_id not in self.recordings:
                logger.warning(f"No active recording for session {session_id}")
                return None
            
            recording = self.recordings[session_id]
            
            # Release video writer
            writer = recording['writer']
            writer.release()
            
            recording['is_recording'] = False
            recording['ended_at'] = datetime.now()
            
            # Calculate duration
            duration = (recording['ended_at'] - recording['started_at']).total_seconds()
            recording['duration_seconds'] = duration
            
            # Get file size
            filepath = Path(recording['filepath'])
            if filepath.exists():
                recording['file_size_bytes'] = filepath.stat().st_size
                recording['file_size_mb'] = recording['file_size_bytes'] / (1024 * 1024)
            
            logger.info(f"Stopped recording for session {session_id}")
            logger.info(f"  Frames: {recording['frame_count']}")
            logger.info(f"  Duration: {duration:.2f}s")
            if 'file_size_mb' in recording:
                logger.info(f"  Size: {recording['file_size_mb']:.2f} MB")
            
            # Remove writer object before returning
            result = {
                'session_id': recording['session_id'],
                'filename': recording['filename'],
                'filepath': recording['filepath'],
                'frame_count': recording['frame_count'],
                'duration_seconds': recording['duration_seconds'],
                'file_size_bytes': recording.get('file_size_bytes', 0),
                'file_size_mb': recording.get('file_size_mb', 0),
                'started_at': recording['started_at'].isoformat(),
                'ended_at': recording['ended_at'].isoformat(),
            }
            
            # Clean up recording entry
            del self.recordings[session_id]
            
            return result
    
    def is_recording(self, session_id: str) -> bool:
        """
        Check if a session is currently recording.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if recording, False otherwise
        """
        with self.lock:
            return session_id in self.recordings and self.recordings[session_id]['is_recording']
    
    def get_recording_info(self, session_id: str) -> Optional[Dict]:
        """
        Get information about an active recording.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Recording info or None if not found
        """
        with self.lock:
            if session_id not in self.recordings:
                return None
            
            recording = self.recordings[session_id]
            
            # Calculate current duration
            current_duration = (datetime.now() - recording['started_at']).total_seconds()
            
            return {
                'session_id': recording['session_id'],
                'filename': recording['filename'],
                'filepath': recording['filepath'],
                'frame_count': recording['frame_count'],
                'duration_seconds': current_duration,
                'fps': recording['fps'],
                'resolution': recording['resolution'],
                'is_recording': recording['is_recording'],
                'started_at': recording['started_at'].isoformat(),
            }
    
    def list_recordings(self) -> list:
        """
        List all video files in the storage directory.
        
        Returns:
            List of recording file information
        """
        recordings = []
        
        for filepath in self.storage_path.glob("*.mp4"):
            stat = filepath.stat()
            recordings.append({
                'filename': filepath.name,
                'filepath': str(filepath),
                'file_size_bytes': stat.st_size,
                'file_size_mb': stat.st_size / (1024 * 1024),
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        # Sort by creation time (newest first)
        recordings.sort(key=lambda x: x['created_at'], reverse=True)
        
        return recordings
    
    def delete_recording(self, filename: str) -> bool:
        """
        Delete a recorded video file.
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        filepath = self.storage_path / filename
        
        if not filepath.exists():
            logger.warning(f"File not found: {filename}")
            return False
        
        try:
            filepath.unlink()
            logger.info(f"Deleted recording: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error deleting {filename}: {e}")
            return False
    
    def cleanup_old_recordings(self, days: int = 7) -> int:
        """
        Delete recordings older than specified days.
        
        Args:
            days: Number of days to keep recordings
            
        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        deleted_count = 0
        
        for filepath in self.storage_path.glob("*.mp4"):
            if filepath.stat().st_mtime < cutoff_time:
                try:
                    filepath.unlink()
                    deleted_count += 1
                    logger.info(f"Cleaned up old recording: {filepath.name}")
                except Exception as e:
                    logger.error(f"Error deleting {filepath.name}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old recordings")
        
        return deleted_count


# Global singleton instance
_video_recording_service: Optional[VideoRecordingService] = None


def get_video_recording_service(storage_path: str = "recordings") -> VideoRecordingService:
    """
    Get or create the global VideoRecordingService instance.
    
    Args:
        storage_path: Base directory for storing videos
        
    Returns:
        VideoRecordingService instance
    """
    global _video_recording_service
    
    if _video_recording_service is None:
        _video_recording_service = VideoRecordingService(storage_path)
    
    return _video_recording_service

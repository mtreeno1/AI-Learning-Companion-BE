"""
Video Recording Router - API endpoints for video recording management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from pathlib import Path
import logging

from app.database import get_db
from app.models.user import User
from app.models.learning_session import LearningSession
from app.models.video_recording import VideoRecording
from app.dependencies import get_current_user
from app.services.video_recording_service import get_video_recording_service
from utils.datetime_utils import now_utc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recordings", tags=["Video Recordings"])


@router.post("/sessions/{session_id}/start")
async def start_recording(
    session_id: UUID,
    fps: Optional[float] = Query(30.0, ge=15.0, le=60.0, description="Frames per second"),
    resolution: Optional[str] = Query("1920x1080", description="Resolution (WIDTHxHEIGHT)"),
    codec: Optional[str] = Query("mp4v", description="Video codec"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start recording video for a learning session.
    
    - **session_id**: Learning session UUID
    - **fps**: Recording FPS (default: 30)
    - **resolution**: Video resolution (default: 1920x1080)
    - **codec**: Video codec (default: mp4v)
    """
    # Verify session exists and belongs to user
    session = db.query(LearningSession).filter(
        LearningSession.session_id == session_id,
        LearningSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if already recording
    existing = db.query(VideoRecording).filter(
        VideoRecording.session_id == session_id,
        VideoRecording.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Recording already active for this session")
    
    # Parse resolution
    try:
        width, height = map(int, resolution.split('x'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid resolution format. Use WIDTHxHEIGHT (e.g., 1920x1080)")
    
    # Start recording service
    video_service = get_video_recording_service()
    
    try:
        recording_info = video_service.start_recording(
            session_id=str(session_id),
            fps=fps,
            resolution=(width, height),
            codec=codec
        )
    except Exception as e:
        logger.error(f"Failed to start recording: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start recording: {str(e)}")
    
    # Save to database
    db_recording = VideoRecording(
        session_id=session_id,
        filename=recording_info['filename'],
        filepath=recording_info['filepath'],
        fps=fps,
        resolution_width=width,
        resolution_height=height,
        codec=codec,
        is_active=True,
        started_at=now_utc()
    )
    
    db.add(db_recording)
    db.commit()
    db.refresh(db_recording)
    
    logger.info(f"Started recording for session {session_id}: {recording_info['filename']}")
    
    return {
        "recording_id": str(db_recording.recording_id),
        "session_id": str(session_id),
        "filename": recording_info['filename'],
        "fps": fps,
        "resolution": f"{width}x{height}",
        "started_at": db_recording.started_at.isoformat(),
        "status": "recording"
    }


@router.post("/sessions/{session_id}/stop")
async def stop_recording(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stop recording video for a learning session.
    
    - **session_id**: Learning session UUID
    """
    # Verify session exists and belongs to user
    session = db.query(LearningSession).filter(
        LearningSession.session_id == session_id,
        LearningSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get active recording
    recording = db.query(VideoRecording).filter(
        VideoRecording.session_id == session_id,
        VideoRecording.is_active == True
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="No active recording for this session")
    
    # Stop recording service
    video_service = get_video_recording_service()
    recording_info = video_service.stop_recording(str(session_id))
    
    if not recording_info:
        raise HTTPException(status_code=500, detail="Failed to stop recording")
    
    # Update database
    recording.is_active = False
    recording.ended_at = now_utc()
    recording.duration_seconds = recording_info.get('duration_seconds', 0)
    recording.frame_count = recording_info.get('frame_count', 0)
    recording.file_size_bytes = recording_info.get('file_size_bytes', 0)
    recording.updated_at = now_utc()
    
    db.commit()
    db.refresh(recording)
    
    logger.info(f"Stopped recording for session {session_id}: {recording.filename}")
    
    return recording.to_dict()


@router.get("/sessions/{session_id}")
async def list_session_recordings(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all recordings for a learning session.
    
    - **session_id**: Learning session UUID
    """
    # Verify session exists and belongs to user
    session = db.query(LearningSession).filter(
        LearningSession.session_id == session_id,
        LearningSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get recordings
    recordings = db.query(VideoRecording).filter(
        VideoRecording.session_id == session_id
    ).order_by(VideoRecording.started_at.desc()).all()
    
    return {
        "session_id": str(session_id),
        "total": len(recordings),
        "recordings": [rec.to_dict() for rec in recordings]
    }


@router.get("/")
async def list_all_recordings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    List all recordings for the current user.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
    """
    # Query recordings through user's sessions
    query = db.query(VideoRecording).join(LearningSession).filter(
        LearningSession.user_id == current_user.id
    )
    
    total = query.count()
    
    offset = (page - 1) * page_size
    recordings = query.order_by(
        VideoRecording.started_at.desc()
    ).offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "recordings": [rec.to_dict() for rec in recordings]
    }


@router.get("/{recording_id}")
async def get_recording(
    recording_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific recording.
    
    - **recording_id**: Recording UUID
    """
    # Get recording and verify access
    recording = db.query(VideoRecording).join(LearningSession).filter(
        VideoRecording.recording_id == recording_id,
        LearningSession.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return recording.to_dict()


@router.get("/{recording_id}/download")
async def download_recording(
    recording_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a recorded video file.
    
    - **recording_id**: Recording UUID
    """
    # Get recording and verify access
    recording = db.query(VideoRecording).join(LearningSession).filter(
        VideoRecording.recording_id == recording_id,
        LearningSession.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Check file exists
    filepath = Path(recording.filepath)
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Return file
    return FileResponse(
        path=str(filepath),
        filename=recording.filename,
        media_type="video/mp4"
    )


@router.delete("/{recording_id}")
async def delete_recording(
    recording_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a recording and its video file.
    
    - **recording_id**: Recording UUID
    """
    # Get recording and verify access
    recording = db.query(VideoRecording).join(LearningSession).filter(
        VideoRecording.recording_id == recording_id,
        LearningSession.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Delete file
    video_service = get_video_recording_service()
    video_service.delete_recording(recording.filename)
    
    # Delete from database
    db.delete(recording)
    db.commit()
    
    logger.info(f"Deleted recording {recording_id}: {recording.filename}")
    
    return {"message": "Recording deleted successfully", "recording_id": str(recording_id)}


@router.get("/{recording_id}/status")
async def get_recording_status(
    recording_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current status of an active recording.
    
    - **recording_id**: Recording UUID
    """
    # Get recording and verify access
    recording = db.query(VideoRecording).join(LearningSession).filter(
        VideoRecording.recording_id == recording_id,
        LearningSession.user_id == current_user.id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # If recording is active, get live stats
    if recording.is_active:
        video_service = get_video_recording_service()
        live_info = video_service.get_recording_info(str(recording.session_id))
        
        if live_info:
            return {
                **recording.to_dict(),
                "live_stats": live_info
            }
    
    return recording.to_dict()

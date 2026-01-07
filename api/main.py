"""
FastAPI REST API for Focus Tracking System

Endpoints:
- POST /api/session/start - Bắt đầu session mới
- POST /api/session/stop - Kết thúc session
- POST /api/frame/process - Xử lý frame và trả về score
- GET /api/session/{session_id} - Lấy thông tin session
- GET /api/session/{session_id}/stats - Thống kê session
- GET /api/sessions - Danh sách tất cả sessions
- WebSocket /ws/focus - Real-time focus tracking
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import cv2
import numpy as np
import base64
from datetime import datetime
import json

from core import FocusScorer, EventDetector, AlertManager
from session_tracker import SessionTracker
from ultralytics import YOLO

# Initialize FastAPI
app = FastAPI(
    title="AI Learning Companion API",
    description="Real-time focus tracking system using YOLO",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên chỉ định cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
det_model = None
pose_model = None
session_tracker = SessionTracker()

# Active sessions storage
active_sessions:  Dict[str, Dict] = {}


# ==================== Pydantic Models ====================

class SessionStartRequest(BaseModel):
    user_id: str
    session_name: Optional[str] = None


class SessionStartResponse(BaseModel):
    session_id: str
    started_at: str
    message: str


class FrameProcessRequest(BaseModel):
    session_id: str
    frame_base64: str  # Base64 encoded image
    timestamp: Optional[float] = None


class FrameProcessResponse(BaseModel):
    session_id: str
    focus_score: float
    focus_level: str
    events:  Dict[str, bool]
    distraction_duration: Optional[float]
    should_alert: bool
    alert_message: Optional[str]
    timestamp: float


class SessionStopRequest(BaseModel):
    session_id: str


class SessionStopResponse(BaseModel):
    session_id: str
    statistics: Dict
    message: str


# ==================== Startup/Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Load YOLO models on startup"""
    global det_model, pose_model
    
    print("🚀 Loading YOLO models...")
    det_model = YOLO("models/yolov8n.pt")
    pose_model = YOLO("models/yolov8n-pose.pt")
    print("✅ Models loaded successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down API...")
    # Save all active sessions
    for session_id in list(active_sessions.keys()):
        _stop_session(session_id)


# ==================== Helper Functions ====================

def decode_base64_frame(base64_str: str) -> np.ndarray:
    """Decode base64 string to numpy array (image)"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        
        img_bytes = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e: 
        raise ValueError(f"Failed to decode frame: {str(e)}")


def encode_frame_to_base64(frame: np.ndarray) -> str:
    """Encode numpy array to base64 string"""
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')


def _stop_session(session_id: str) -> Dict:
    """Internal function to stop session"""
    if session_id not in active_sessions:
        return None
    
    session_data = active_sessions[session_id]
    scorer = session_data['scorer']
    
    # Get final statistics
    stats = scorer.get_session_stats()
    
    # Save to tracker
    session_tracker.save_session(
        session_id=session_id,
        user_id=session_data['user_id'],
        session_name=session_data.get('session_name'),
        scorer=scorer
    )
    
    # Remove from active sessions
    del active_sessions[session_id]
    
    return stats


# ==================== REST Endpoints ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AI Learning Companion API",
        "version": "1.0.0",
        "active_sessions": len(active_sessions)
    }


@app.post("/api/session/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    """
    Bắt đầu session tracking mới
    """
    # Generate session ID
    session_id = session_tracker.create_session_id(request.user_id)
    
    # Initialize components
    scorer = FocusScorer()
    detector = EventDetector()
    alert_manager = AlertManager()
    
    # Store in active sessions
    active_sessions[session_id] = {
        'session_id': session_id,
        'user_id': request.user_id,
        'session_name':  request.session_name,
        'started_at': datetime.now().isoformat(),
        'scorer': scorer,
        'detector': detector,
        'alert_manager': alert_manager,
    }
    
    return SessionStartResponse(
        session_id=session_id,
        started_at=active_sessions[session_id]['started_at'],
        message="Session started successfully"
    )


@app.post("/api/frame/process", response_model=FrameProcessResponse)
async def process_frame(request: FrameProcessRequest):
    """
    Xử lý một frame và trả về kết quả focus score
    """
    # Check if session exists
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = active_sessions[request.session_id]
    scorer = session_data['scorer']
    detector = session_data['detector']
    alert_manager = session_data['alert_manager']
    
    # Decode frame
    try:
        frame = decode_base64_frame(request.frame_base64)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Run detection
    det_results = det_model(frame, conf=0.5, verbose=False)
    pose_results = pose_model(frame, verbose=False)
    
    # Detect events
    events = detector.detect_events(frame, det_results, pose_results, det_model, pose_model)
    
    # Update focus score
    focus_score = scorer.update(events)
    level, _ = scorer.get_focus_level()
    
    # Check for alerts
    distraction_duration = scorer.get_distraction_duration()
    should_alert = alert_manager.should_alert(focus_score, distraction_duration)
    alert_message = None
    
    if should_alert:
        alert_message = alert_manager.get_alert_message(focus_score, level)
    
    return FrameProcessResponse(
        session_id=request.session_id,
        focus_score=focus_score,
        focus_level=level,
        events=events,
        distraction_duration=distraction_duration,
        should_alert=should_alert,
        alert_message=alert_message,
        timestamp=request.timestamp or datetime.now().timestamp()
    )


@app.post("/api/session/stop", response_model=SessionStopResponse)
async def stop_session(request: SessionStopRequest):
    """
    Kết thúc session và lưu statistics
    """
    stats = _stop_session(request.session_id)
    
    if stats is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionStopResponse(
        session_id=request.session_id,
        statistics=stats,
        message="Session stopped and saved successfully"
    )


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """
    Lấy thông tin session (active hoặc saved)
    """
    # Check active sessions
    if session_id in active_sessions:
        session_data = active_sessions[session_id]
        scorer = session_data['scorer']
        
        return {
            "session_id": session_id,
            "user_id": session_data['user_id'],
            "session_name": session_data.get('session_name'),
            "status": "active",
            "started_at": session_data['started_at'],
            "current_score": scorer.score,
            "current_level": scorer.get_focus_level()[0],
        }
    
    # Check saved sessions
    session = session_tracker.get_session(session_id)
    if session:
        return session
    
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/session/{session_id}/stats")
async def get_session_stats(session_id: str):
    """
    Lấy thống kê chi tiết của session
    """
    # Check active sessions
    if session_id in active_sessions:
        scorer = active_sessions[session_id]['scorer']
        return scorer.get_session_stats()
    
    # Check saved sessions
    session = session_tracker.get_session(session_id)
    if session and 'statistics' in session:
        return session['statistics']
    
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/sessions")
async def list_sessions(user_id: Optional[str] = None, limit: int = 50):
    """
    Danh sách tất cả sessions (active + saved)
    """
    result = {
        'active': [],
        'saved': []
    }
    
    # Active sessions
    for session_id, session_data in active_sessions.items():
        if user_id is None or session_data['user_id'] == user_id:
            result['active'].append({
                'session_id': session_id,
                'user_id': session_data['user_id'],
                'session_name': session_data.get('session_name'),
                'started_at': session_data['started_at'],
                'status': 'active'
            })
    
    # Saved sessions
    saved = session_tracker.get_user_sessions(user_id, limit=limit) if user_id else session_tracker.get_all_sessions(limit=limit)
    result['saved'] = saved
    
    return result


# ==================== WebSocket for Real-time Tracking ====================

@app.websocket("/ws/focus/{session_id}")
async def websocket_focus_tracking(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time focus tracking
    
    Client sends:  {"frame":  "base64_encoded_image"}
    Server sends: {
        "focus_score": 85.5,
        "focus_level": "focused",
        "events": {...},
        "should_alert": false
    }
    """
    await websocket.accept()
    
    # Check if session exists
    if session_id not in active_sessions:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return
    
    session_data = active_sessions[session_id]
    scorer = session_data['scorer']
    detector = session_data['detector']
    alert_manager = session_data['alert_manager']
    
    try:
        while True:
            # Receive frame from client
            data = await websocket.receive_json()
            
            if 'frame' not in data: 
                await websocket.send_json({"error": "No frame provided"})
                continue
            
            # Decode frame
            try:
                frame = decode_base64_frame(data['frame'])
            except ValueError as e: 
                await websocket.send_json({"error": str(e)})
                continue
            
            # Run detection
            det_results = det_model(frame, conf=0.5, verbose=False)
            pose_results = pose_model(frame, verbose=False)
            
            # Detect events
            events = detector.detect_events(frame, det_results, pose_results, det_model, pose_model)
            
            # Update focus score
            focus_score = scorer.update(events)
            level, color = scorer.get_focus_level()
            
            # Check for alerts
            distraction_duration = scorer.get_distraction_duration()
            should_alert = alert_manager.should_alert(focus_score, distraction_duration)
            alert_message = None
            
            if should_alert: 
                alert_message = alert_manager.get_alert_message(focus_score, level)
            
            # Send response
            await websocket.send_json({
                "focus_score": round(focus_score, 1),
                "focus_level":  level,
                "color": color,
                "events":  events,
                "distraction_duration": distraction_duration,
                "should_alert": should_alert,
                "alert_message": alert_message,
                "timestamp": datetime.now().timestamp()
            })
            
    except WebSocketDisconnect: 
        print(f"WebSocket disconnected for session:  {session_id}")
    except Exception as e:
        print(f"WebSocket error:  {str(e)}")
        await websocket.close()


# ==================== Development Endpoints ====================

@app.get("/api/debug/sessions")
async def debug_sessions():
    """Debug endpoint to see all active session details"""
    return {
        session_id: {
            'user_id': data['user_id'],
            'started_at': data['started_at'],
            'current_score': data['scorer'].score,
            'history_length': len(data['scorer'].history)
        }
        for session_id, data in active_sessions.items()
    }


if __name__ == "__main__": 
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
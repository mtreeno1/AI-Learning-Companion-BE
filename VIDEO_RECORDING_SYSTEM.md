# Video Recording System Documentation

## Overview

The AI Learning Companion now includes a backend video recording system that enables high-quality video recording without overloading the browser.This implementation follows best practices for computer vision systems.

## Architecture

### Key Principles (from requirements)

1.**Backend Processing (Server-Side)** - Best Solution

- Video processing is done on the server using OpenCV
- High-quality recording (Full HD, configurable FPS)
- Videos saved directly to disk storage
- Can be extended to cloud storage (S3, Azure Blob)

2.**Optimized Browser Streaming**

- Browser sends low FPS snapshots (5 FPS) via WebSocket
- Server records at high FPS (30 FPS) while processing snapshots
- Only metadata and detection results sent back to browser
- Minimal browser overhead

3.**Workflow**

```
Camera (Browser) → WebSocket (5 FPS snapshots) → Server
                                                   ↓
                                     AI Detection + Recording (30 FPS)
                                                   ↓
                                     Save to Disk (MP4)
                                                   ↓
Browser ← Detection Results + Stats ← Server
```

## Components

### 1.VideoRecordingService (`app/services/video_recording_service.py`)

Core service for managing video recording:

**Features:**

- Start/stop recording for sessions
- Configurable FPS, resolution, codec
- Thread-safe operations
- Automatic frame writing
- File management and cleanup

**Default Configuration:**

```python
{
    'fps': 30.0,           # High FPS for quality
    'resolution': (1920, 1080),  # Full HD
    'codec': 'mp4v',       # H.264 compatible
    'quality': 95          # High quality
}
```

**Usage:**

```python
from app.services.video_recording_service import get_video_recording_service

service = get_video_recording_service()

# Start recording
info = service.start_recording(
    session_id="session-uuid",
    fps=30.0,
    resolution=(1920, 1080)
)

# Write frames during detection
service.write_frame(session_id, frame_array)

# Stop recording
result = service.stop_recording(session_id)
```

### 2.VideoRecording Model (`app/models/video_recording.py`)

Database model for storing recording metadata:

**Fields:**

- `recording_id`: Unique identifier
- `session_id`: Link to learning session
- `filename`, `filepath`: File information
- `fps`, `resolution_width`, `resolution_height`: Recording settings
- `duration_seconds`, `frame_count`: Recording metrics
- `file_size_bytes`: Storage size
- `cloud_storage_url`, `cloud_storage_provider`: Optional cloud storage

### 3.Recording API Endpoints (`app/routers/recordings.py`)

RESTful API for managing recordings:

#### Start Recording

```http
POST /api/recordings/sessions/{session_id}/start
Authorization: Bearer <token>
Query Parameters:
  - fps: 30.0 (default, range: 15-60)
  - resolution: "1920x1080" (default)
  - codec: "mp4v" (default)
```

#### Stop Recording

```http
POST /api/recordings/sessions/{session_id}/stop
Authorization: Bearer <token>
```

#### List Recordings

```http
GET /api/recordings/sessions/{session_id}
GET /api/recordings/  # All user recordings
Authorization: Bearer <token>
```

#### Download Recording

```http
GET /api/recordings/{recording_id}/download
Authorization: Bearer <token>
```

#### Delete Recording

```http
DELETE /api/recordings/{recording_id}
Authorization: Bearer <token>
```

### 4.WebSocket Integration

The WebSocket endpoint (`/api/focus/ws/{session_id}`) has been enhanced:

**Query Parameter:**

- `enable_recording`: Boolean to enable frame writing

**Behavior:**
1.Browser sends frames at 5 FPS (200ms interval)
2.Server writes frames to video file at 30 FPS (interpolates/duplicates frames)
3.Server runs AI detection on each frame
4.Server sends detection results + recording status back

**Response includes:**

```json
{
  "recording": {
    "enabled": true,
    "active": true
  }
  // ...other detection data
}
```

## Usage Flow

### 1.Start a Session with Recording

**Frontend:**

```javascript
// Create session
const response = await fetch("http://localhost:8000/api/focus/sessions", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    session_name: "Study Session",
    subject: "Math",
    initial_score: 100,
  }),
});
const { session_id } = await response.json();

// Start recording
await fetch(
  `http://localhost:8000/api/recordings/sessions/${session_id}/start?fps=30&resolution=1920x1080`,
  {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  }
);

// Connect WebSocket with recording enabled
const ws = new WebSocket(
  `ws://localhost:8000/api/focus/ws/${session_id}?enable_recording=true`
);
```

### 2.During Session

- Browser captures and sends frames at 5 FPS
- Server writes frames to video file at 30 FPS
- Server performs AI detection
- Browser receives detection results

### 3.End Session

**Frontend:**

```javascript
// Stop recording
await fetch(
  `http://localhost:8000/api/recordings/sessions/${session_id}/stop`,
  {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  }
);

// End session
await fetch(`http://localhost:8000/api/focus/sessions/${session_id}/end`, {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` },
  body: JSON.stringify({ status: "completed" }),
});

// Close WebSocket
ws.close();
```

### 4.View/Download Recording

**Frontend:**

```javascript
// List recordings
const recordings = await fetch(
  `http://localhost:8000/api/recordings/sessions/${session_id}`,
  {
    headers: { Authorization: `Bearer ${token}` },
  }
);

// Download
window.open(
  `http://localhost:8000/api/recordings/${recording_id}/download`,
  "_blank"
);
```

## Storage

### Local Storage

- Videos stored in `recordings/` directory
- Filename format: `session_{session_id}_{timestamp}.mp4`
- Automatic directory creation on startup

### Cloud Storage (Future Enhancement)

The system is designed to support cloud storage:

```python
# Example S3 integration (future)
def upload_to_s3(filepath, session_id):
    s3_client.upload_file(
        filepath,
        bucket_name,
        f"recordings/{session_id}.mp4"
    )
    return s3_url
```

Update the `VideoRecording` model:

```python
recording.cloud_storage_url = s3_url
recording.cloud_storage_provider = 's3'
```

## Performance Optimization

### Browser Side

- **Low FPS streaming**: 5 FPS reduces bandwidth
- **JPEG compression**: 0.8 quality for snapshots
- **Canvas-based capture**: Efficient frame extraction
- **WebSocket**: Persistent connection, low overhead

### Server Side

- **High FPS recording**: 30 FPS for smooth playback
- **Batch commits**: Database updates every 5 frames
- **Thread-safe**: Multiple sessions can record simultaneously
- **Frame interpolation**: Duplicates frames to reach target FPS

### Benefits

1.**Browser doesn't freeze**: Only 5 FPS upload 2.**High-quality recording**: 30 FPS on server 3.**Scalable**: Server handles heavy lifting 4.**Efficient storage**: H.264 codec compression

## Configuration

### Environment Variables

Add to `.env` or configuration:

```bash
# Video Recording Settings
RECORDINGS_PATH=recordings
RECORDING_DEFAULT_FPS=30.0
RECORDING_DEFAULT_RESOLUTION=1920x1080
RECORDING_DEFAULT_CODEC=mp4v
RECORDING_RETENTION_DAYS=7

# Storage
ENABLE_CLOUD_STORAGE=false
S3_BUCKET_NAME=your-bucket
S3_REGION=us-east-1
AZURE_STORAGE_CONNECTION_STRING=your-connection
```

### Cleanup

Automatic cleanup of old recordings:

```python
from app.services.video_recording_service import get_video_recording_service

service = get_video_recording_service()
deleted = service.cleanup_old_recordings(days=7)
print(f"Cleaned up {deleted} recordings older than 7 days")
```

## Dependencies

Already installed:

- `opencv-python`: Video encoding/decoding
- `numpy`: Frame manipulation
- `fastapi`: API endpoints
- `sqlalchemy`: Database ORM

## Testing

### Test Recording Service

```python
import cv2
import numpy as np
from app.services.video_recording_service import VideoRecordingService

service = VideoRecordingService("test_recordings")

# Start recording
info = service.start_recording("test-session", fps=30, resolution=(640, 480))

# Write test frames
for i in range(90):  # 3 seconds at 30 FPS
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    service.write_frame("test-session", frame)

# Stop
result = service.stop_recording("test-session")
print(f"Recorded {result['frame_count']} frames in {result['duration_seconds']:.2f}s")
```

### Test API

```bash
# Start recording
curl -X POST "http://localhost:8000/api/recordings/sessions/{session_id}/start?fps=30&resolution=1920x1080" \
  -H "Authorization: Bearer <token>"

# Stop recording
curl -X POST "http://localhost:8000/api/recordings/sessions/{session_id}/stop" \
  -H "Authorization: Bearer <token>"

# List recordings
curl "http://localhost:8000/api/recordings/" \
  -H "Authorization: Bearer <token>"

# Download
curl "http://localhost:8000/api/recordings/{recording_id}/download" \
  -H "Authorization: Bearer <token>" \
  -o recording.mp4
```

## Security Considerations

1.**Authentication**: All endpoints require JWT token 2.**Authorization**: Users can only access their own recordings 3.**Path Validation**: Filenames validated to prevent path traversal 4.**File Cleanup**: Automatic deletion of old files 5.**Storage Limits**: Consider implementing quota per user

## Future Enhancements

1.**Cloud Storage Integration**

- AWS S3
- Azure Blob Storage
- Google Cloud Storage

2.**Advanced Features**

- Video streaming (HLS/DASH)
- Real-time transcoding
- Thumbnail generation
- Frame extraction for analysis

3.**Optimization**

- Hardware acceleration (GPU)
- H.265 codec support
- Adaptive bitrate
- Multi-resolution recording

4.**Analytics**

- Storage usage monitoring
- Recording quality metrics
- Bandwidth usage tracking

## Troubleshooting

### Recording Fails to Start

- Check `recordings/` directory exists and is writable
- Verify OpenCV is installed: `pip install opencv-python`
- Check logs for codec errors

### Large File Sizes

- Reduce FPS: `fps=15`
- Reduce resolution: `resolution=1280x720`
- Use better codec: `codec=avc1` (if available)

### WebSocket Disconnects

- Check keepalive is working
- Verify network stability
- Increase WebSocket timeout

### Frame Writing Errors

- Check disk space
- Verify file permissions
- Monitor memory usage

## Summary

The video recording system provides:

- ✅ Server-side video recording (no browser overload)
- ✅ High-quality storage (Full HD, 30 FPS)
- ✅ Efficient streaming (5 FPS to browser)
- ✅ RESTful API for management
- ✅ Database tracking
- ✅ Easy retrieval and playback
- ✅ Extensible to cloud storage

This implementation follows the requirements for optimal real-time video recording in computer vision systems.

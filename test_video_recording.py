#!/usr/bin/env python3
"""
Test Video Recording Service - Standalone test without dependencies on FastAPI/DB

This script tests the core video recording functionality without requiring
a full server setup.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import cv2
        print("✅ OpenCV (cv2) imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import cv2: {e}")
        print("   Run: pip install opencv-python")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import numpy: {e}")
        return False
    
    return True


def test_video_recording_service():
    """Test the VideoRecordingService class"""
    print("\n" + "="*60)
    print("Testing VideoRecordingService")
    print("="*60)
    
    try:
        from app.services.video_recording_service import VideoRecordingService
        print("✅ VideoRecordingService imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import VideoRecordingService: {e}")
        return False
    
    # Create test service
    import tempfile
    import shutil
    
    test_dir = tempfile.mkdtemp(prefix="test_recordings_")
    print(f"📁 Using test directory: {test_dir}")
    
    try:
        service = VideoRecordingService(storage_path=test_dir)
        print("✅ Service initialized")
        
        # Test starting recording
        session_id = "test-session-123"
        recording_info = service.start_recording(
            session_id=session_id,
            fps=10.0,
            resolution=(640, 480),
            codec='mp4v'
        )
        print(f"✅ Recording started: {recording_info['filename']}")
        
        # Test writing frames
        import cv2
        import numpy as np
        
        print("📝 Writing test frames...")
        for i in range(30):  # 3 seconds at 10 FPS
            # Create a test frame with frame number
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, f"Frame {i}", (200, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            
            success = service.write_frame(session_id, frame)
            if not success:
                print(f"❌ Failed to write frame {i}")
                break
        
        print(f"✅ Wrote 30 test frames")
        
        # Test getting recording info
        info = service.get_recording_info(session_id)
        print(f"✅ Recording info: {info['frame_count']} frames, {info['duration_seconds']:.2f}s")
        
        # Test stopping recording
        result = service.stop_recording(session_id)
        print(f"✅ Recording stopped:")
        print(f"   - Frames: {result['frame_count']}")
        print(f"   - Duration: {result['duration_seconds']:.2f}s")
        print(f"   - File size: {result['file_size_mb']:.2f} MB")
        
        # Verify file exists
        import os
        if os.path.exists(result['filepath']):
            print(f"✅ Video file created: {result['filepath']}")
        else:
            print(f"❌ Video file not found: {result['filepath']}")
            return False
        
        # Test listing recordings
        recordings = service.list_recordings()
        print(f"✅ Found {len(recordings)} recordings")
        
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"✅ Cleaned up test directory")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        
        return False


def test_model_structure():
    """Test if the VideoRecording model is properly defined"""
    print("\n" + "="*60)
    print("Testing VideoRecording Model Structure")
    print("="*60)
    
    try:
        from app.models.video_recording import VideoRecording
        print("✅ VideoRecording model imported successfully")
        
        # Check key attributes
        required_attrs = [
            'recording_id', 'session_id', 'filename', 'filepath',
            'fps', 'resolution_width', 'resolution_height',
            'duration_seconds', 'frame_count', 'is_active'
        ]
        
        for attr in required_attrs:
            if hasattr(VideoRecording, attr):
                print(f"  ✅ {attr}")
            else:
                print(f"  ❌ {attr} missing")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import VideoRecording model: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("🧪 Video Recording System Tests")
    print("="*60)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import tests failed. Install missing dependencies.")
        return False
    
    # Test 2: Model structure
    if not test_model_structure():
        print("\n❌ Model structure tests failed.")
        return False
    
    # Test 3: Video recording service
    if not test_video_recording_service():
        print("\n❌ Video recording service tests failed.")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\n📝 Summary:")
    print("  - Core dependencies are available")
    print("  - Model structure is correct")
    print("  - Video recording service works properly")
    print("  - Frame writing and file creation successful")
    print("\n🎉 The video recording system is ready to use!")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

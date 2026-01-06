# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.config import settings
# from app.database import init_db
# from app.routers import auth_router

# # Initialize database
# init_db()

# # Create FastAPI application
# app = FastAPI(
#    title="FocusFlow API",
#    description="Authentication and services API for FocusFlow AI Learning Companion",
#    version="1.0.0"
# )

# # Configure CORS
# app.add_middleware(
#    CORSMiddleware,
#    allow_origins=settings.cors_origins_list,
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
# )

# # Include routers
# app.include_router(auth_router)


# @app.get("/")
# def read_root():
#    """Health check endpoint"""
#    return {
#        "status": "ok",
#        "service": "FocusFlow API",
#        "version": "1.0.0",
#        "database": "PostgreSQL"
#    }


# @app.get("/health")
# def health_check():
#    """Detailed health check"""
#    return {
#        "status": "healthy",
#        "database": "connected",
#        "api_version": "1.0.0"
#    }


# if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run(
#        "app.main:app",
#        host=settings.API_HOST,
#        port=settings.API_PORT,
#        reload=True
#    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import auth_router
from app.routers. focus import router as focus_router  # ✅ Make sure this line exists
from app.routers.recordings import router as recordings_router

# Initialize database
init_db()

# Create FastAPI application
app = FastAPI(
    title="FocusFlow API",
    description="Authentication and AI Focus Detection API for FocusFlow Learning Companion",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, tags=["Authentication"])
app.include_router(focus_router, tags=["Focus Detection"])
app.include_router(recordings_router, tags=["Video Recordings"])

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "FocusFlow API",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("🚀 FocusFlow API Starting")
    print("=" * 60)
    
    try:
        from app.models.user import User
        from app.models.learning_session import LearningSession
        from app.models.video_recording import VideoRecording
        from app. database import Base, engine
        
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables ready")
    except Exception as e:
        print(f"⚠️  Database error: {e}")
    
    # Create recordings directory
    try:
        from pathlib import Path
        recordings_dir = Path("recordings")
        recordings_dir.mkdir(exist_ok=True)
        print(f"✅ Recordings directory ready: {recordings_dir.absolute()}")
    except Exception as e:
        print(f"⚠️  Failed to create recordings directory: {e}")
    
    print(f"📍 Server: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 Docs:    http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
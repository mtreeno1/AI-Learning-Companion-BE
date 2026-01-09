from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings

# Base class for models
Base = declarative_base()

# Create engine and session lazily to avoid startup failures
engine = None
SessionLocal = None

def get_engine():
    """Get or create database engine"""
    global engine
    if engine is None:
        engine = create_engine(
            settings.DATABASE_URL,
            poolclass=NullPool
        )
    return engine

def get_session_local():
    """Get or create session factory"""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return SessionLocal


def get_db():
   """
   Dependency for getting database session
   """
   session_local = get_session_local()
   db = session_local()
   try:
       yield db
   finally:
       db.close()


def init_db():
   """
   Initialize database tables
   Non-blocking: logs errors but doesn't crash the application
   """
   try:
       # Import all models to ensure tables are created
       from app.models import user, session
       from app.models.learning_session import LearningSession
       from app.models.video_recording import VideoRecording
       
       db_engine = get_engine()
       Base.metadata.create_all(bind=db_engine)
   except Exception as e:
       print(f"⚠️  init_db failed: {e}")
       # Don't raise the exception - allow app to start
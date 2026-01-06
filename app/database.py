from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
   """
   Dependency for getting database session
   """
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()


def init_db():
   """
   Initialize database tables
   """
   from app.models import user, session  # Import all models
   Base.metadata.create_all(bind=engine)
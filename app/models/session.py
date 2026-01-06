from sqlalchemy import Column, String, DateTime
from app.database import Base


class SessionToken(Base):
   __tablename__ = "sessions"
   
   token = Column(String, primary_key=True, index=True)
   user_id = Column(String, nullable=False)
   email = Column(String, nullable=False)
   expires_at = Column(DateTime, nullable=False)
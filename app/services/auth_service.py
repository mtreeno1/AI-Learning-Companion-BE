from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.user import User
from app.models.session import SessionToken
from app.dependencies import (
    hash_password,
    verify_password,
    generate_token
)
from app.config import settings
from jose import jwt

class AuthService:
    """Service for handling authentication logic"""
    
    @staticmethod
    def signup(db: Session, name: str, email: str, password: str) -> dict:
        """Register new user and return JWT token"""
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_pwd = hash_password(password)
        
        # ✅ Create new user WITHOUT id parameter
        # SQLAlchemy will auto-generate UUID via default=uuid.uuid4
        new_user = User(
            # ❌ DELETE:  id=generate_user_id()
            email=email,
            name=name,
            password=hashed_pwd,
            created_at=datetime.utcnow()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)  # ✅ After this, new_user.id will have UUID value
        
        # ✅ Debug
        print(f"✅ Created user: {new_user.email}")
        print(f"✅ User ID: {new_user.id} (type: {type(new_user.id)})")
        
        # ✅ Create JWT token
        access_token_expires = timedelta(days=settings.TOKEN_EXPIRY_DAYS)
        expire = datetime.utcnow() + access_token_expires
        
        to_encode = {
            "sub": str(new_user.id),  # ✅ Convert UUID to string
            "email": new_user.email,
            "name": new_user.name,
            "exp": expire,
        }
        
        print(f"✅ JWT payload: {to_encode}")
        
        access_token = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        print(f"✅ Generated JWT: {access_token[:50]}...")
        
        return {
            "id": str(new_user.id),  # ✅ Convert UUID to string for JSON
            "email": new_user.email,
            "name": new_user.name,
            "token": access_token
        }
    
    @staticmethod
    def login(db:  Session, email: str, password:  str) -> dict:
        """Login user and return JWT token"""
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # ✅ CREATE JWT TOKEN (NOT SESSION TOKEN)
        access_token_expires = timedelta(days=settings.TOKEN_EXPIRY_DAYS)
        expire = datetime.utcnow() + access_token_expires
        
        # ✅ Create payload
        to_encode = {
            "sub": str(user.id),  # ✅ IMPORTANT: user.id as string
            "email": user.email,
            "name": user.name,
            "exp": expire,
        }
        
        # ✅ Encode JWT
        access_token = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        # ✅ Debug logging
        print(f"✅ Login successful for:  {user.email}")
        print(f"✅ Generated JWT token with {len(access_token.split('.'))} parts")
        print(f"✅ Token preview: {access_token[:50]}...")
        
        return {
            "id": user.id,
            "email": user.email,
            "name":  user.name,
            "token": access_token  # ✅ Return JWT token
        }
    
    @staticmethod
    def logout(db: Session, token: str) -> dict:
        session = db.query(SessionToken).filter(SessionToken.token == token).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        db.delete(session)
        db.commit()
        
        return {"message": "Logged out successfully"}
    
    @staticmethod
    def verify_token(db: Session, token: str) -> dict:
        session = db.query(SessionToken).filter(SessionToken.token == token).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Check if token is expired
        if datetime.utcnow() > session.expires_at:
            db.delete(session)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        
        # Get user info
        user = db.query(User).filter(User.email == session.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "token": token
        }
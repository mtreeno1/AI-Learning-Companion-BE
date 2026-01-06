# from passlib.context import CryptContext
# import secrets

# pwd_context = CryptContext(
#     schemes=["argon2"],
#     deprecated="auto"
# )

# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)

# def verify_password(password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(password, hashed_password)

# def generate_token() -> str:
#     return secrets.token_urlsafe(32)

# def generate_user_id() -> str:
#     return secrets.token_urlsafe(16)


"""
Dependencies for FastAPI routes
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets

from app.config import settings
from app.database import get_db
from app.models.user import User

# Password hashing
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

# JWT Bearer token scheme
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(password, hashed_password)


def generate_token() -> str:
    """Generate a random token"""
    return secrets.token_urlsafe(32)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate":  "Bearer"},
    )
    
    try:
        token = credentials.credentials
        
        # ✅ Debug
        print(f"Received token: {token[: 50]}...")
        print(f"Token parts: {len(token.split('.'))}")
        
        # ✅ Validate JWT format
        if len(token.split('.')) != 3:
            print(f"❌ Invalid JWT format: only {len(token.split('.'))} parts")
            raise credentials_exception
        
        # ✅ Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        print(f"✅ Decoded payload: {payload}")
        
        # ✅ Extract user_id from 'sub' claim
        user_id:  str = payload.get("sub")
        if user_id is None:
            print("❌ No 'sub' claim in token")
            raise credentials_exception
        
            
    except JWTError as e: 
        print(f"❌ JWT decode error: {str(e)}")
        raise credentials_exception
    
    # ✅ Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        print(f"❌ User not found with id: {user_id}")
        raise credentials_exception
    
    print(f"✅ User authenticated: {user.email}")
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User | None:
    """
    Optional authentication - returns None if no valid token
    """
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None
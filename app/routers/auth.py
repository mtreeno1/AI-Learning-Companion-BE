from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.auth import (
   SignupRequest,
   LoginRequest,
   LogoutRequest,
   UserResponse,
   MessageResponse
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
   """
   Register a new user
   
   - **name**: User's full name
   - **email**: User's email address
   - **password**: Password (minimum 6 characters)
   """
   try:
        result = AuthService.signup(
            db=db,
            name=request.name,
            email=request.email,
            password=request.password
        )
        return UserResponse(**result)
   except Exception as e:
        import traceback
        print(f"Signup error: {str(e)}")
        print(traceback.format_exc())
        raise


@router.post("/login", response_model=UserResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
   """
   Login an existing user
   
   - **email**: User's email address
   - **password**: User's password
   """
   result = AuthService.login(
       db=db,
       email=request.email,
       password=request.password
   )
   return UserResponse(**result)


@router.post("/logout", response_model=MessageResponse)
def logout(request: LogoutRequest, db: Session = Depends(get_db)):
   """
   Logout a user by invalidating their session
   
   - **token**: Session token to invalidate
   """
   result = AuthService.logout(db=db, token=request.token)
   return MessageResponse(**result)


@router.get("/verify", response_model=UserResponse)
def verify_token(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
   """
   Verify a session token and return user info
   
   **Headers:**
   - **Authorization**: ******
   """
   from fastapi import HTTPException
   
   if not authorization or not authorization.startswith("Bearer "):
       raise HTTPException(
           status_code=status.HTTP_401_UNAUTHORIZED,
           detail="Invalid authorization header"
       )
   
   token = authorization.replace("Bearer ", "")
   result = AuthService.verify_token(db=db, token=token)
   return UserResponse(**result)
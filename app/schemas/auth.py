from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.dialects.postgresql import UUID

class SignupRequest(BaseModel):
   """Request schema for user signup"""
   name: str = Field(..., min_length=1, max_length=100)
   email: EmailStr
   password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
   """Request schema for user login"""
   email: EmailStr
   password: str = Field(..., min_length=6)


class LogoutRequest(BaseModel):
   """Request schema for user logout"""
   token: str


class UserResponse(BaseModel):
   """Response schema for user data"""
   email: str
   name: str
   token: str


class MessageResponse(BaseModel):
   """Generic message response"""
   message: str
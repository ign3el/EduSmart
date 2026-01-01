import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from auth import create_access_token, verify_token
from database_models import User, UserOperations

logger = logging.getLogger(__name__)

# Create a new router for auth endpoints
router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

# --- Pydantic Models for clean API contracts ---

class SignupRequest(BaseModel):
    """Request model for user signup."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, description="Must be between 3 and 50 characters.")
    password: str = Field(..., min_length=6, max_length=100, description="Must be at least 6 characters.")

class UserResponse(BaseModel):
    """Response model for user data, excluding sensitive information."""
    id: int
    email: EmailStr
    username: str
    is_verified: bool
    is_premium: bool

    class Config:
        from_attributes = True # Allows mapping from ORM models or dicts

class TokenResponse(BaseModel):
    """Response model for JWT token."""
    access_token: str
    token_type: str = "bearer"

# --- Dependency for authentication ---

# This dependency will look for a bearer token in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current user from a JWT token.
    Raises 401 Unauthorized if the token is invalid, expired, or user not found.
    """
    email = verify_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = UserOperations.get_by_email(email)
    if not user:
        # This can happen if the user was deleted after the token was issued.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# --- Authentication Endpoints ---

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest):
    """
    Handles user registration.
    Checks for existing email/username and creates a new user if they don't exist.
    """
    logger.info(f"Signup attempt for email: {request.email}, username: {request.username}")
    
    # Check if a user with that email or username already exists to provide a clear error.
    if UserOperations.get_by_email(request.email) or UserOperations.get_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email or username already exists.",
        )
    
    # Create the user in the database
    user = UserOperations.create(
        email=request.email,
        username=request.username,
        password=request.password
    )
    
    # This should not happen if the checks above are correct, but as a safeguard:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the user.",
        )
        
    # Here you would typically trigger an email verification flow.
    # For now, we just log and return the user.
    # e.g., token = UserOperations.create_verification_token(user['id'])
    # e.g., send_verification_email(user['email'], token)
    
    logger.info(f"User '{user['username']}' created successfully (ID: {user['id']}).")
    return user

@router.post("/token", response_model=TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Handles user login via standard OAuth2 form data.
    Verifies credentials and returns a JWT access token.
    Note: The 'username' field of the form is used for the user's email.
    """
    user = UserOperations.authenticate(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Optional: Check if the user's email has been verified.
    # This is a good security practice.
    if not user['is_verified']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox for a verification link.",
        )
    
    logger.info(f"User '{user['email']}' authenticated successfully.")
    
    # The 'sub' (subject) of the token is the user's email.
    access_token = create_access_token(data={"sub": user['email']})
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Returns the data for the currently authenticated user.
    This is a protected endpoint.
    """
    return current_user

import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, validator

from auth import create_access_token, verify_token, generate_secure_token
from database_models import User, UserOperations
from services.email_service import send_verification_email, send_password_reset_email

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
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$", description="3-50 characters, alphanumeric and underscores only")
    password: str = Field(..., min_length=8, max_length=100, description="Minimum 8 characters")
    confirm_password: str = Field(..., description="Must match password")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def password_complexity(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserResponse(BaseModel):
    """Response model for user data, excluding sensitive information."""
    id: int
    email: EmailStr
    username: str
    is_verified: bool
    is_premium: bool
    is_admin: bool

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
        
    # Create verification token and send email
    try:
        token = UserOperations.create_verification_token(user['id'])
        send_verification_email(user['email'], token)
        logger.info(f"Verification email sent to {user['email']}")
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        # Don't fail signup if email fails, user can resend later
    
    logger.info(f"User '{user['username']}' created successfully (ID: {user['id']}).")
    return user

@router.post("/token", response_model=TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Handles user login via standard OAuth2 form data.
    Verifies credentials and returns a JWT access token.
    Note: The 'username' field accepts EITHER username OR email.
    """
    # Try to authenticate with either email or username
    user = None
    if '@' in form_data.username:
        # Looks like an email
        user = UserOperations.authenticate(email=form_data.username, password=form_data.password)
    else:
        # Looks like a username
        user = UserOperations.authenticate_by_username(username=form_data.username, password=form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User found: {user['email']}, is_verified: {user.get('is_verified', False)}")
        
    # Optional: Check if the user's email has been verified.
    # This is a good security practice.
    if not user['is_verified']:
        logger.warning(f"Login blocked for unverified user: {user['email']}")
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

@router.post("/resend-verification", status_code=status.HTTP_200_OK)
def resend_verification_email(email: EmailStr):
    """
    Resends the verification email. Has a 3-minute cooldown to prevent abuse.
    """
    user = UserOperations.get_by_email(email)
    if not user:
        # Don't reveal whether email exists for security
        return {"message": "If this email is registered, a verification link has been sent."}
    
    if user['is_verified']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Check cooldown (3 minutes)
    cooldown_seconds = UserOperations.check_verification_cooldown(user['id'])
    if cooldown_seconds > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {cooldown_seconds} seconds before resending email"
        )
    
    try:
        token = UserOperations.create_verification_token(user['id'])
        UserOperations.track_verification_email_sent(user['id'])
        send_verification_email(email, token)
        logger.info(f"Verification email resent to {email}")
        return {"message": "Verification email sent successfully"}
    except Exception as e:
        logger.error(f"Failed to resend verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )

@router.get("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(token: str):
    """
    Verifies a user's email address using the token from the verification email.
    """
    user_id = UserOperations.verify_email_with_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    logger.info(f"Email verified for user ID: {user_id}")
    return {"message": "Email verified successfully"}

class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password."""
    email: EmailStr

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(request: ForgotPasswordRequest):
    """
    Sends a password reset email to the user.
    Always returns success to avoid revealing which emails are registered.
    """
    user = UserOperations.get_by_email(request.email)
    
    # Always return success, don't reveal if email exists
    if not user:
        logger.info(f"Password reset requested for non-existent email: {request.email}")
        return {"message": "If this email is registered, a password reset link has been sent."}
    
    try:
        token = UserOperations.create_password_reset_token(user['id'])
        send_password_reset_email(request.email, token)
        logger.info(f"Password reset email sent to {request.email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        # Still return success to avoid revealing email existence
    
    return {"message": "If this email is registered, a password reset link has been sent."}

class ResetPasswordRequest(BaseModel):
    """Request model for password reset."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def password_complexity(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(request: ResetPasswordRequest):
    """
    Resets a user's password using a valid reset token.
    """
    user_id = UserOperations.verify_reset_token(request.token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update the password
    from auth import get_password_hash
    password_hash = get_password_hash(request.new_password)
    
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (password_hash, user_id)
            )
            # Delete the used token
            cursor.execute(
                "DELETE FROM password_reset_tokens WHERE user_id = %s",
                (user_id,)
            )
        
        logger.info(f"Password reset successful for user ID: {user_id}")
        return {"message": "Password reset successfully"}
    except Exception as e:
        logger.error(f"Failed to reset password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

# Import get_db_cursor at the top if not already imported
from database import get_db_cursor

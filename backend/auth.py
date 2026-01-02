"""
Clean implementation of authentication utilities:
- JWT token generation and verification
- Password hashing and verification with bcrypt
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, use system environment variables
    pass

from jose import JWTError, jwt
from passlib.context import CryptContext

# --- Configuration ---
# It is CRITICAL that JWT_SECRET is set in a production environment.
DEFAULT_INSECURE_SECRET_KEY = "a-very-insecure-secret-key-please-change-me"
JWT_SECRET = os.getenv("JWT_SECRET", DEFAULT_INSECURE_SECRET_KEY)

if JWT_SECRET == DEFAULT_INSECURE_SECRET_KEY:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("!!! WARNING: JWT_SECRET is not set in your environment or .env file.         !!!")
    print("!!! Using a default, insecure key. This is NOT SAFE for production.         !!!")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# --- Password Hashing ---
# Create a password context for bcrypt.
# This handles all the complexity of salting and hashing.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Hashes a password using bcrypt.
    
    This function correctly handles the 72-byte limit of the bcrypt algorithm
    by encoding the password to UTF-8 and then truncating to 72 bytes before hashing.
    """
    password_bytes = password.encode('utf-8')
    # bcrypt has a hard 72-byte limit. We truncate the password bytes to prevent an error.
    truncated_bytes = password_bytes[:72]
    # Decode back to string because passlib expects a string, not bytes
    truncated_string = truncated_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(truncated_string)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed password.
    
    Uses the same truncation logic as get_password_hash to ensure consistency.
    """
    password_bytes = plain_password.encode('utf-8')
    truncated_bytes = password_bytes[:72]
    # Decode back to string because passlib expects a string, not bytes
    truncated_string = truncated_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(truncated_string, hashed_password)

# --- JWT Token Handling ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token containing the provided data.
    
    Args:
        data: A dictionary of claims to include in the token (e.g., {'sub': user_email}).
        expires_delta: An optional timedelta for when the token should expire. 
                       Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.
                       
    Returns:
        The encoded JWT as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """
    Verifies a JWT token.
    
    If the token is valid and not expired, it returns the subject ('sub') claim.
    Otherwise, it returns None.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        # 'sub' (subject) is a standard JWT claim. We use it for the user's identifier (e.g., email).
        subject = payload.get("sub")
        if subject is None:
            return None
        return subject
    except JWTError:
        # This catches various errors like invalid signature, expired token, etc.
        return None

# --- Generic Token Generation ---
def generate_secure_token() -> str:
    """
    Generates a cryptographically secure, URL-safe random token.
    This can be used for email verification links, password reset tokens, etc.
    """
    return secrets.token_urlsafe(32)
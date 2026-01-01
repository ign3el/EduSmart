"""
Authentication utilities: JWT tokens, password hashing, email verification
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import secrets
import bcrypt
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
# passlib expects bcrypt.__about__.__version__; some builds of the bcrypt
# package omit __about__, so we patch it to avoid runtime errors.
if not hasattr(bcrypt, "__about__"):
    class _About:
        __version__ = getattr(bcrypt, "__version__", "0")
    bcrypt.__about__ = _About()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (bcrypt limit is 72 bytes)"""
    # Truncate to 72 bytes to comply with bcrypt limitation
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password (bcrypt limit is 72 bytes)"""
    # Debug: log password length before truncation
    password_bytes = password.encode('utf-8')
    print(f"[PASSWORD DEBUG] Received password length: {len(password_bytes)} bytes")
    print(f"[PASSWORD DEBUG] Password repr: {repr(password)}")
    
    if len(password_bytes) > 72:
        print(f"[PASSWORD DEBUG] Truncating from {len(password_bytes)} to 72 bytes")
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_verification_token() -> str:
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)


def create_verification_link(token: str, base_url: str = "https://edusmart.ign3el.com") -> str:
    """Create an email verification link"""
    return f"{base_url}/verify-email?token={token}"

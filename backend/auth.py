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

# Ensure passlib-compatible bcrypt metadata exists on both bcrypt and _bcrypt
try:
    import _bcrypt as _bcrypt  # type: ignore
except ImportError:  # pragma: no cover - if C backend missing, passlib will use pure Python
    _bcrypt = None
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
# passlib expects bcrypt.__about__.__version__; some builds omit it.
class _About:
    __version__ = getattr(bcrypt, "__version__", "0")

if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = _About()  # type: ignore

if _bcrypt and not hasattr(_bcrypt, "__about__"):
    _bcrypt.__about__ = _About()  # type: ignore

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash, truncating to 72 bytes for bcrypt."""
    password_bytes = plain_password.encode('utf-8')
    # Truncate to 72 bytes
    truncated_bytes = password_bytes[:72]
    # Decode back to string for passlib, ignoring errors if truncation breaks a multi-byte char
    password_to_verify = truncated_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(password_to_verify, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password, truncating to 72 bytes for bcrypt compatibility."""
    password_bytes = password.encode('utf-8')
    # Truncate to 72 bytes
    truncated_bytes = password_bytes[:72]
    # Decode back to string for passlib, ignoring errors if truncation breaks a multi-byte char
    password_to_hash = truncated_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password_to_hash)


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

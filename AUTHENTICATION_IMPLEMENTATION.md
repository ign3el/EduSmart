# EduSmart User Authentication Implementation Guide

## 🎯 What's Been Done

### Backend Setup (Completed)
1. ✅ **Installed Dependencies**
   - mysql-connector-python - MySQL database connector
   - PyJWT - JWT token generation
   - python-jose - JWT encryption
   - passlib[bcrypt] - Password hashing
   - fastapi-mail - Email sending

2. ✅ **Created Core Files**
   - `backend/database.py` - MySQL connection pooling & table initialization
   - `backend/auth.py` - JWT tokens, password hashing, verification utilities
   - `backend/models.py` - User & Story database operations
   - Updated `backend/requirements.txt`
   - Added DB config to `backend/.env`

3. ✅ **Database Schema**
   - `users` table (id, email, username, password_hash, is_verified, is_premium, timestamps)
   - `email_verifications` table (token management)
   - `user_stories` table (user-specific story storage with JSON data)

---

## 🚀 Next Steps (TODO)

### 1. Configure Database Connection
**File: `backend/.env`**

Update these values with your actual MySQL credentials:
```bash
MYSQL_USER=your_actual_db_username
MYSQL_PASSWORD=your_actual_db_password
MYSQL_DATABASE=edusmart_db  # or your preferred DB name
JWT_SECRET=$(openssl rand -hex 32)  # Generate a secure secret
MAIL_USERNAME=your_gmail@gmail.com
MAIL_PASSWORD=your_gmail_app_password
```

### 2. Add Authentication Endpoints to main.py
**File: `backend/main.py`**

Add these imports at the top:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from models import UserOperations, StoryOperations
from auth import create_access_token, verify_token
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
```

Add authentication endpoints:
```python
# Security
security = HTTPBearer()

# Email configuration
mail_config = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=bool(os.getenv("MAIL_STARTTLS", "True")),
    MAIL_SSL_TLS=bool(os.getenv("MAIL_SSL_TLS", "False")),
    USE_CREDENTIALS=True
)

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = UserOperations.get_user_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# Request/Response models
class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# AUTH ENDPOINTS

@app.post("/api/auth/signup")
async def signup(data: SignupRequest):
    """Register a new user"""
    # Validate input
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Create user
    user_id = UserOperations.create_user(data.email, data.username, data.password)
    if not user_id:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    
    # Generate verification token
    token = UserOperations.create_verification_token(user_id)
    verification_link = f"{os.getenv('APP_URL')}/verify-email?token={token}"
    
    # Send verification email
    message = MessageSchema(
        subject="Verify Your EduSmart Account",
        recipients=[data.email],
        body=f"""
        <html>
            <body>
                <h2>Welcome to EduSmart!</h2>
                <p>Thanks for signing up, {data.username}!</p>
                <p>Please click the link below to verify your email:</p>
                <a href="{verification_link}">Verify Email</a>
                <p>This link expires in 24 hours.</p>
            </body>
        </html>
        """,
        subtype="html"
    )
    
    try:
        fm = FastMail(mail_config)
        await fm.send_message(message)
    except Exception as e:
        print(f"Failed to send email: {e}")
    
    return {"message": "User created. Please check your email to verify your account."}

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """Login user"""
    user = UserOperations.authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user['is_verified']:
        raise HTTPException(status_code=403, detail="Please verify your email first")
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user['id'])})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user['id'],
            "email": user['email'],
            "username": user['username'],
            "is_premium": user['is_premium']
        }
    }

@app.get("/api/auth/verify-email")
async def verify_email(token: str):
    """Verify email with token"""
    user_id = UserOperations.verify_email_token(token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    return {"message": "Email verified successfully! You can now login."}

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user['id'],
        "email": current_user['email'],
        "username": current_user['username'],
        "is_verified": current_user['is_verified'],
        "is_premium": current_user['is_premium']
    }
```

### 3. Update Story Endpoints to Require Authentication
**File: `backend/main.py`**

Modify existing story endpoints:

```python
# BEFORE (old):
@app.post("/api/save-story/{job_id}")
async def save_story(job_id: str, story_name: str = Form(...)):
    # ... old code

# AFTER (new):
@app.post("/api/save-story/{job_id}")
async def save_story(
    job_id: str, 
    story_name: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Save story to user's account"""
    job_data = jobs.get(job_id)
    if not job_data or job_data["status"] != "completed":
        raise HTTPException(status_code=404, detail="Story not found or not ready")
    
    story_id = f"user_{current_user['id']}_{int(time.time() * 1000)}"
    success = StoryOperations.save_story(
        user_id=current_user['id'],
        story_id=story_id,
        name=story_name,
        story_data=job_data["story_data"]
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save story")
    
    return {"story_id": story_id, "message": "Story saved successfully"}

@app.get("/api/list-stories")
async def list_stories(current_user: dict = Depends(get_current_user)):
    """List all stories for current user"""
    stories = StoryOperations.get_user_stories(current_user['id'])
    return stories

@app.get("/api/load-story/{story_id}")
async def load_story(story_id: str, current_user: dict = Depends(get_current_user)):
    """Load a specific story"""
    story = StoryOperations.get_story(current_user['id'], story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@app.delete("/api/delete-story/{story_id}")
async def delete_story(story_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a story"""
    success = StoryOperations.delete_story(current_user['id'], story_id)
    if not success:
        raise HTTPException(status_code=404, detail="Story not found")
    return {"message": "Story deleted successfully"}
```

---

## 📱 Frontend Implementation (Major Work Ahead)

### 4. Create Authentication Components

Create these new files in `frontend/src/components/`:

1. **Login.jsx** - Login form
2. **Signup.jsx** - Registration form
3. **EmailVerification.jsx** - Email verification handler
4. **UserProfile.jsx** - User profile page
5. **ProtectedRoute.jsx** - Route guard for authenticated pages

### 5. Create Auth Context
**File: `frontend/src/context/AuthContext.jsx`**

Create context for global auth state management.

### 6. Update App Routing
**File: `frontend/src/App.jsx`**

Add authentication routes and protect existing routes.

### 7. Update API Calls
Update all story-related API calls to include JWT token in headers.

---

## 🔐 Security Notes

1. **JWT Secret**: Generate with `openssl rand -hex 32`
2. **Password Requirements**: Minimum 8 characters (consider adding complexity rules)
3. **Email Verification**: Required before login
4. **Token Expiry**: 7 days (configurable in auth.py)
5. **HTTPS**: Ensure production uses HTTPS only

---

## 📊 Database Migration

Existing stories in filesystem need to be migrated to database when users first login:
- Create migration script
- Match stories by job_id or timestamp
- Associate with user_id

---

## ⚠️ Important Next Actions

1. **Update `.env` with real database credentials**
2. **Test database connection**: Run `python backend/database.py`
3. **Add authentication endpoints to `main.py`**
4. **Test signup flow**: curl or Postman
5. **Build frontend auth components**
6. **Test end-to-end auth flow**

---

## 📞 Support

For issues:
1. Check database connection
2. Verify .env configuration
3. Check MySQL user permissions
4. Test email sending (Gmail requires App Password)


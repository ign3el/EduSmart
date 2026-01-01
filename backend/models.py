"""
User database operations
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from database import get_db_cursor
from auth import get_password_hash, verify_password, generate_verification_token
import mysql.connector


class UserOperations:
    @staticmethod
    def create_user(email: str, username: str, password: str) -> Optional[int]:
        """Create a new user"""
        try:
            password_hash = get_password_hash(password)
            with get_db_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO users (email, username, password_hash) 
                       VALUES (%s, %s, %s)""",
                    (email.lower(), username, password_hash)
                )
                return cursor.lastrowid
        except mysql.connector.IntegrityError:
            return None  # User already exists
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE email = %s",
                (email.lower(),)
            )
            return cursor.fetchone()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, email, username, is_verified, is_premium, created_at FROM users WHERE id = %s",
                (user_id,)
            )
            return cursor.fetchone()
    
    @staticmethod
    def verify_user(user_id: int) -> bool:
        """Mark user as verified"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET is_verified = TRUE WHERE id = %s",
                    (user_id,)
                )
                return cursor.rowcount > 0
        except:
            return False
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        user = UserOperations.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user['password_hash']):
            return None
        return user
    
    @staticmethod
    def create_verification_token(user_id: int) -> str:
        """Create email verification token"""
        token = generate_verification_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        with get_db_cursor() as cursor:
            # Delete old tokens
            cursor.execute(
                "DELETE FROM email_verifications WHERE user_id = %s",
                (user_id,)
            )
            # Insert new token
            cursor.execute(
                """INSERT INTO email_verifications (user_id, token, expires_at) 
                   VALUES (%s, %s, %s)""",
                (user_id, token, expires_at)
            )
        return token
    
    @staticmethod
    def verify_email_token(token: str) -> Optional[int]:
        """Verify email token and return user_id"""
        with get_db_cursor() as cursor:
            cursor.execute(
                """SELECT user_id FROM email_verifications 
                   WHERE token = %s AND expires_at > NOW()""",
                (token,)
            )
            result = cursor.fetchone()
            if result:
                user_id = result['user_id']
                # Delete used token
                cursor.execute(
                    "DELETE FROM email_verifications WHERE token = %s",
                    (token,)
                )
                # Mark user as verified
                UserOperations.verify_user(user_id)
                return user_id
            return None


class StoryOperations:
    @staticmethod
    def save_story(user_id: int, story_id: str, name: str, story_data: dict) -> bool:
        """Save a story for a user"""
        try:
            import json
            with get_db_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO user_stories (user_id, story_id, name, story_data) 
                       VALUES (%s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE name = VALUES(name), story_data = VALUES(story_data), updated_at = CURRENT_TIMESTAMP""",
                    (user_id, story_id, name, json.dumps(story_data))
                )
                return True
        except Exception as e:
            print(f"Error saving story: {e}")
            return False
    
    @staticmethod
    def get_user_stories(user_id: int):
        """Get all stories for a user"""
        import json
        with get_db_cursor() as cursor:
            cursor.execute(
                """SELECT id, story_id, name, created_at, updated_at 
                   FROM user_stories WHERE user_id = %s 
                   ORDER BY updated_at DESC""",
                (user_id,)
            )
            stories = cursor.fetchall()
            # Convert timestamp to string for JSON serialization
            for story in stories:
                if 'created_at' in story and story['created_at']:
                    story['saved_at'] = str(int(story['created_at'].timestamp() * 1000))
                if 'updated_at' in story:
                    story['updated_at'] = story['updated_at'].isoformat() if story['updated_at'] else None
                if 'created_at' in story:
                    story['created_at'] = story['created_at'].isoformat() if story['created_at'] else None
            return stories
    
    @staticmethod
    def get_story(user_id: int, story_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific story"""
        import json
        with get_db_cursor() as cursor:
            cursor.execute(
                """SELECT story_id as id, name, story_data, created_at 
                   FROM user_stories 
                   WHERE user_id = %s AND story_id = %s""",
                (user_id, story_id)
            )
            story = cursor.fetchone()
            if story and 'story_data' in story:
                story['story_data'] = json.loads(story['story_data']) if isinstance(story['story_data'], str) else story['story_data']
                if 'created_at' in story and story['created_at']:
                    story['saved_at'] = str(int(story['created_at'].timestamp() * 1000))
            return story
    
    @staticmethod
    def delete_story(user_id: int, story_id: str) -> bool:
        """Delete a story"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    "DELETE FROM user_stories WHERE user_id = %s AND story_id = %s",
                    (user_id, story_id)
                )
                return cursor.rowcount > 0
        except:
            return False

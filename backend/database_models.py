"""
Database models and operations for users and stories.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, TypedDict
import logging
import json
import mysql.connector

from database import get_db_cursor
from auth import get_password_hash, verify_password, generate_secure_token

logger = logging.getLogger(__name__)

class User(TypedDict):
    id: int
    email: str
    username: str
    password_hash: str
    is_verified: bool
    is_premium: bool
    created_at: datetime
    updated_at: datetime

class UserOperations:
    @staticmethod
    def create(email: str, username: str, password: str) -> Optional[User]:
        """Creates a new user in the database."""
        password_hash = get_password_hash(password)
        try:
            with get_db_cursor(commit=True) as cursor:
                query = "INSERT INTO users (email, username, password_hash) VALUES (%s, %s, %s)"
                cursor.execute(query, (email.lower(), username, password_hash))
                
                if cursor.rowcount == 0:
                    logger.error("User creation failed unexpectedly (rowcount is 0).")
                    return None

                user_id = cursor.lastrowid
                logger.info(f"User '{username}' created with ID: {user_id}")
                
                # Construct a partial User object. This is more efficient than calling get_by_id.
                new_user: User = {
                    "id": user_id,
                    "email": email.lower(),
                    "username": username,
                    "is_verified": False,
                    "is_premium": False,
                }
                return new_user
        except mysql.connector.IntegrityError:
            logger.warning(f"IntegrityError on user creation for '{username}'. Likely a duplicate email or username.")
            return None
        except mysql.connector.Error as err:
            logger.error(f"Database error during user creation for '{username}': {err}")
            return None

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """Retrieves a user by their email address."""
        try:
            with get_db_cursor() as cursor:
                query = "SELECT * FROM users WHERE email = %s"
                cursor.execute(query, (email.lower(),))
                return cursor.fetchone()
        except mysql.connector.Error as err:
            logger.error(f"Database error getting user by email: {err}")
            return None

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """Retrieves a user by their username."""
        try:
            with get_db_cursor() as cursor:
                query = "SELECT * FROM users WHERE username = %s"
                cursor.execute(query, (username,))
                return cursor.fetchone()
        except mysql.connector.Error as err:
            logger.error(f"Database error getting user by username: {err}")
            return None

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """Retrieves a user by their ID."""
        try:
            with get_db_cursor() as cursor:
                query = "SELECT * FROM users WHERE id = %s"
                cursor.execute(query, (user_id,))
                return cursor.fetchone()
        except mysql.connector.Error as err:
            logger.error(f"Database error getting user by ID: {err}")
            return None

    @staticmethod
    def authenticate(email: str, password: str) -> Optional[User]:
        """Authenticates a user by email and password. Returns the user object if successful."""
        user = UserOperations.get_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user['password_hash']):
            return None
            
        return user

    @staticmethod
    def create_verification_token(user_id: int) -> str:
        """Creates and stores a new email verification token for a user."""
        token = generate_secure_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("DELETE FROM email_verifications WHERE user_id = %s", (user_id,))
                query = "INSERT INTO email_verifications (user_id, token, expires_at) VALUES (%s, %s, %s)"
                cursor.execute(query, (user_id, token, expires_at))
            return token
        except mysql.connector.Error as err:
            logger.error(f"Database error creating verification token: {err}")
            raise

    @staticmethod
    def set_verified(user_id: int) -> bool:
        """Marks a user's email as verified in the database."""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("UPDATE users SET is_verified = TRUE WHERE id = %s", (user_id,))
                return cursor.rowcount > 0
        except mysql.connector.Error as err:
            logger.error(f"Database error setting verified status: {err}")
            return False

    @staticmethod
    def verify_email_with_token(token: str) -> Optional[int]:
        """
        Verifies an email token. If valid, marks user as verified and deletes the token.
        Returns the user_id if successful, otherwise None.
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                query = "SELECT user_id FROM email_verifications WHERE token = %s AND expires_at > NOW()"
                cursor.execute(query, (token,))
                result = cursor.fetchone()
                
                if not result:
                    return None
                    
                user_id = result['user_id']
                
                if UserOperations.set_verified(user_id):
                    logger.info(f"Email successfully verified for user ID: {user_id}")
                    cursor.execute("DELETE FROM email_verifications WHERE token = %s", (token,))
                    return user_id
                else:
                    return None
        except mysql.connector.Error as err:
            logger.error(f"Database error verifying token: {err}")
            return None

class StoryOperations:
    @staticmethod
    def save_story(user_id: int, story_id: str, name: str, story_data: dict) -> bool:
        """Save a story for a user"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """INSERT INTO user_stories (user_id, story_id, name, story_data) 
                       VALUES (%s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE name = VALUES(name), story_data = VALUES(story_data), updated_at = CURRENT_TIMESTAMP""",
                    (user_id, story_id, name, json.dumps(story_data))
                )
                return True
        except mysql.connector.Error as e:
            logger.error(f"Error saving story: {e}")
            return False
    
    @staticmethod
    def get_user_stories(user_id: int):
        """Get all stories for a user"""
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
                if 'updated_at' in story and story['updated_at']:
                    story['updated_at'] = story['updated_at'].isoformat() if story['updated_at'] else None
                if 'created_at' in story:
                    story['created_at'] = story['created_at'].isoformat() if story['created_at'] else None
            return stories
    
    @staticmethod
    def get_story(user_id: int, story_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific story"""
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
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    "DELETE FROM user_stories WHERE user_id = %s AND story_id = %s",
                    (user_id, story_id)
                )
                return cursor.rowcount > 0
        except mysql.connector.Error as e:
            logger.error(f"Error deleting story: {e}")
            return False
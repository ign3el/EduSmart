"""
Database models and operations for users and stories.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import json
import mysql.connector

from database import get_db_cursor
from auth import get_password_hash, verify_password, generate_secure_token

logger = logging.getLogger(__name__)

# Use Dict instead of TypedDict to avoid required field errors
User = Dict[str, Any]

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
    def authenticate_by_username(username: str, password: str) -> Optional[User]:
        """Authenticates a user by username and password. Returns the user object if successful."""
        user = UserOperations.get_by_username(username)
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
                rows_affected = cursor.rowcount
                logger.info(f"set_verified for user {user_id}: {rows_affected} rows updated")
                return rows_affected > 0
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
                # Check if token exists and is not expired
                query = "SELECT user_id FROM email_verifications WHERE token = %s AND expires_at > NOW()"
                cursor.execute(query, (token,))
                result = cursor.fetchone()
                
                if not result:
                    logger.warning(f"Verification token not found or expired: {token[:20]}...")
                    return None
                    
                user_id = result['user_id']
                logger.info(f"Found verification token for user ID: {user_id}")
                
                # Update user's is_verified status
                cursor.execute("UPDATE users SET is_verified = TRUE WHERE id = %s", (user_id,))
                rows_updated = cursor.rowcount
                logger.info(f"Updated is_verified for user {user_id}: {rows_updated} rows affected")
                
                if rows_updated > 0:
                    # Delete the used token
                    cursor.execute("DELETE FROM email_verifications WHERE token = %s", (token,))
                    logger.info(f"✅ Email successfully verified for user ID: {user_id}")
                    return user_id
                else:
                    logger.error(f"Failed to update is_verified for user {user_id}")
                    return None
        except mysql.connector.Error as err:
            logger.error(f"Database error verifying token: {err}")
            return None
    
    @staticmethod
    def create_password_reset_token(user_id: int) -> str:
        """Creates and stores a new password reset token for a user."""
        token = generate_secure_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        
        try:
            with get_db_cursor(commit=True) as cursor:
                # Delete any existing tokens for this user
                cursor.execute("DELETE FROM password_reset_tokens WHERE user_id = %s", (user_id,))
                query = "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)"
                cursor.execute(query, (user_id, token, expires_at))
            return token
        except mysql.connector.Error as err:
            logger.error(f"Database error creating password reset token: {err}")
            raise
    
    @staticmethod
    def verify_reset_token(token: str) -> Optional[int]:
        """
        Verifies a password reset token and returns the user_id if valid.
        Does not delete the token - that should be done after password is successfully reset.
        """
        try:
            with get_db_cursor() as cursor:
                query = "SELECT user_id FROM password_reset_tokens WHERE token = %s AND expires_at > NOW()"
                cursor.execute(query, (token,))
                result = cursor.fetchone()
                return result['user_id'] if result else None
        except mysql.connector.Error as err:
            logger.error(f"Database error verifying reset token: {err}")
            return None
    
    @staticmethod
    def track_verification_email_sent(user_id: int) -> None:
        """Records when a verification email was sent for cooldown tracking."""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    "UPDATE users SET last_verification_sent = NOW() WHERE id = %s",
                    (user_id,)
                )
        except mysql.connector.Error as err:
            logger.error(f"Database error tracking verification email: {err}")
    
    @staticmethod
    def check_verification_cooldown(user_id: int) -> int:
        """
        Checks if a user is in the cooldown period for resending verification emails.
        Returns the number of seconds remaining in cooldown, or 0 if no cooldown.
        """
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    "SELECT last_verification_sent FROM users WHERE id = %s",
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if not result or not result['last_verification_sent']:
                    return 0
                
                last_sent = result['last_verification_sent']
                cooldown_duration = timedelta(minutes=3)
                time_since_last = datetime.utcnow() - last_sent
                
                if time_since_last < cooldown_duration:
                    remaining = cooldown_duration - time_since_last
                    return int(remaining.total_seconds())
                
                return 0
        except mysql.connector.Error as err:
            logger.error(f"Database error checking verification cooldown: {err}")
            return 0

class StoryOperations:

    @staticmethod

    def save_story(user_id: int, story_id: str, name: str, story_data: dict) -> bool:

        """Save a story for a specific user."""

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

            logger.error(f"Error saving story for user {user_id}: {e}")

            return False

    

    @staticmethod

    def get_user_stories(user_id: int) -> list:

        """Get all stories for a specific user."""

        try:

            with get_db_cursor() as cursor:

                query = """

                    SELECT id, story_id, name, created_at, updated_at 

                    FROM user_stories 

                    WHERE user_id = %s 

                    ORDER BY updated_at DESC

                """

                cursor.execute(query, (user_id,))

                stories = cursor.fetchall()

                for story in stories:

                    if story.get('created_at'):

                        story['saved_at'] = str(int(story['created_at'].timestamp() * 1000))

                        story['created_at'] = story['created_at'].isoformat()

                    if story.get('updated_at'):

                        story['updated_at'] = story['updated_at'].isoformat()

                return stories

        except mysql.connector.Error as e:

            logger.error(f"Error getting stories for user {user_id}: {e}")

            return []



    @staticmethod

    def get_all_stories() -> list:

        """(Admin only) Gets all stories from all users, including the creator's username."""

        try:

            with get_db_cursor() as cursor:

                query = """
                    SELECT s.id, s.story_id, s.name, s.created_at, s.updated_at, u.username
                    FROM user_stories s
                    LEFT JOIN users u ON s.user_id = u.id
                    ORDER BY s.updated_at DESC
                """

                cursor.execute(query)

                stories = cursor.fetchall()

                for story in stories:

                    if story.get('created_at'):

                        story['saved_at'] = str(int(story['created_at'].timestamp() * 1000))

                        story['created_at'] = story['created_at'].isoformat()

                    if story.get('updated_at'):

                        story['updated_at'] = story['updated_at'].isoformat()

                return stories

        except mysql.connector.Error as e:

            logger.error(f"Error getting all stories for admin: {e}")

            return []

    

    @staticmethod

    def get_story(story_id: str, user: User) -> Optional[Dict[str, Any]]:

        """

        Gets a specific story. Admins can get any story, while regular users can only get their own.

        """

        try:

            with get_db_cursor() as cursor:

                query = "SELECT us.* FROM user_stories us WHERE us.story_id = %s"

                params = [story_id]

                

                if not user.get('is_admin'):

                    query += " AND us.user_id = %s"

                    params.append(user['id'])

                    

                cursor.execute(query, tuple(params))

                story = cursor.fetchone()

                

                if not story:

                    return None

                    

                if story.get('story_data') and isinstance(story['story_data'], str):

                    story['story_data'] = json.loads(story['story_data'])

                if story.get('created_at'):

                    story['saved_at'] = str(int(story['created_at'].timestamp() * 1000))



                return story

        except mysql.connector.Error as e:

            logger.error(f"Error getting story {story_id}: {e}")

            return None

    

    @staticmethod

    def delete_story(story_id: str, user: User) -> bool:

        """

        Deletes a story. Admins can delete any story, while regular users can only delete their own.

        """

        try:

            with get_db_cursor(commit=True) as cursor:

                query = "DELETE FROM user_stories WHERE story_id = %s"

                params = [story_id]



                if not user.get('is_admin'):

                    query += " AND user_id = %s"

                    params.append(user['id'])



                cursor.execute(query, tuple(params))

                return cursor.rowcount > 0

        except mysql.connector.Error as e:

            logger.error(f"Error deleting story {story_id}: {e}")

            return False

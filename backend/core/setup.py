"""
Application setup utilities, including initial user creation.
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from the root .env file
# This is important for when this module is used outside the main app context
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

from database import get_db_cursor, initialize_database
from auth import get_password_hash

logger = logging.getLogger(__name__)

# --- Admin User Configuration ---
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "edusmart@ign3el.com")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Bhilai-9") # IMPORTANT: Change this in a production environment via .env

def create_admin_user():
    """
    Checks for and creates a default admin user with elevated privileges.
    This function is idempotent and safe to run on every application startup.
    """
    if not ADMIN_PASSWORD:
        logger.warning("ADMIN_PASSWORD is not set. Skipping admin user creation.")
        return

    logger.info("Checking for admin user presence...")
    
    try:
        # Ensure the tables exist first
        initialize_database()

        with get_db_cursor(commit=True) as cursor:
            # Check if an admin with this email or username already exists
            cursor.execute("SELECT id, username, email, is_admin FROM users WHERE email = %s OR username = %s", (ADMIN_EMAIL, ADMIN_USERNAME))
            existing_user = cursor.fetchone()

            if existing_user:
                if existing_user['is_admin']:
                    logger.info(f"✓ Admin user '{existing_user['username']}' already exists. No action needed.")
                else:
                    # If a non-admin user has the credentials, upgrade them
                    logger.warning(f"User '{existing_user['username']}' exists but is not an admin. Upgrading privileges...")
                    cursor.execute("UPDATE users SET is_admin = TRUE, is_verified = TRUE WHERE id = %s", (existing_user['id'],))
                    logger.info(f"✓ User '{existing_user['username']}' has been promoted to admin.")
                return

            # If user does not exist, create them
            logger.info("Admin user not found. Creating a new admin account...")
            password_hash = get_password_hash(ADMIN_PASSWORD)

            query = """
                INSERT INTO users (email, username, password_hash, is_verified, is_admin)
                VALUES (%s, %s, %s, TRUE, TRUE)
            """
            cursor.execute(query, (ADMIN_EMAIL, ADMIN_USERNAME, password_hash))
            
            if cursor.rowcount > 0:
                logger.info("✓ ADMIN USER CREATED SUCCESSFULLY")
                logger.info(f"  - Username: {ADMIN_USERNAME}")
                logger.info("  - NOTE: Password is set from ADMIN_PASSWORD environment variable.")
            else:
                logger.error("✗ Admin user creation failed for an unknown reason.")

    except Exception as e:
        logger.error(f"AN ERROR OCCURRED during admin user setup: {e}")
        logger.error("Please check your database connection settings and ensure the database server is running.")


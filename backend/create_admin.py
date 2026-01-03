"""
One-time script to create an admin user for the EduStory application.

This script is safe to run multiple times. It will only create the admin
user if a user with the specified admin email or username does not already exist.
"""
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the Python path to allow for package-like imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from the root .env file
# This must be done before importing database or auth modules
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
if os.path.exists(dotenv_path):
    print(f"Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print("Warning: .env file not found at project root. Script may fail to connect to DB.")

from database import get_db_cursor, initialize_database
from auth import get_password_hash

# --- Admin User Configuration ---
ADMIN_EMAIL = "admin@edusmart.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin" # IMPORTANT: Change this in a production environment

def create_admin_user():
    """
    Checks for and creates a default admin user with elevated privileges.
    """
    print("--- Admin User Setup ---")
    
    try:
        # First, ensure the tables exist
        print("Initializing database schema if not present...")
        initialize_database()

        with get_db_cursor(commit=True) as cursor:
            # Check if an admin with this email or username already exists
            print(f"Checking for existing user: {ADMIN_USERNAME} / {ADMIN_EMAIL}")
            cursor.execute("SELECT id, username, email, is_admin FROM users WHERE email = %s OR username = %s", (ADMIN_EMAIL, ADMIN_USERNAME))
            existing_user = cursor.fetchone()

            if existing_user:
                if existing_user['is_admin']:
                    print(f"✓ Admin user '{existing_user['username']}' already exists. No action needed.")
                else:
                    # If a non-admin user has the credentials, upgrade them
                    print(f"User '{existing_user['username']}' exists but is not an admin. Upgrading privileges...")
                    cursor.execute("UPDATE users SET is_admin = TRUE, is_verified = TRUE WHERE id = %s", (existing_user['id'],))
                    print(f"✓ User '{existing_user['username']}' has been promoted to admin.")
                return

            # If user does not exist, create them
            print("Admin user not found. Creating a new admin account...")
            password_hash = get_password_hash(ADMIN_PASSWORD)

            query = """
                INSERT INTO users (email, username, password_hash, is_verified, is_admin)
                VALUES (%s, %s, %s, TRUE, TRUE)
            """
            cursor.execute(query, (ADMIN_EMAIL, ADMIN_USERNAME, password_hash))
            
            if cursor.rowcount > 0:
                print("\n" + "="*30)
                print("✓ ADMIN USER CREATED SUCCESSFULLY")
                print("="*30)
                print(f"  - Username: {ADMIN_USERNAME}")
                print(f"  - Email:    {ADMIN_EMAIL}")
                print(f"  - Password: {ADMIN_PASSWORD}")
                print("\nIMPORTANT: Please change the default password after your first login.")
            else:
                print("✗ Admin user creation failed for an unknown reason.")

    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
        print("Please check your database connection settings in the .env file and ensure the database server is running.")

if __name__ == "__main__":
    create_admin_user()

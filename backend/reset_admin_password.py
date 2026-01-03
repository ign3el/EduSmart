"""
Reset admin password directly in the database.
Run this on the VPS: docker exec -it edusmart-backend-1 python reset_admin_password.py
"""
import sys
from getpass import getpass
from auth import get_password_hash
from database_models import UserOperations
from database import get_db_cursor
import mysql.connector

def reset_admin_password():
    print("="*60)
    print("Reset Admin Password")
    print("="*60)
    
    # Get new password
    password = getpass("Enter new admin password: ")
    password_confirm = getpass("Confirm password: ")
    
    if password != password_confirm:
        print("❌ Passwords don't match!")
        return False
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters!")
        return False
    
    # Hash the password
    hashed_password = get_password_hash(password)
    
    # Update admin user
    try:
        with get_db_cursor() as cursor:
            # Find admin user
            cursor.execute("SELECT id, email, username FROM users WHERE is_admin = 1 LIMIT 1")
            admin = cursor.fetchone()
            
            if not admin:
                print("❌ No admin user found in database!")
                return False
            
            print(f"\nFound admin: {admin['username']} ({admin['email']})")
            
            # Update password
            cursor.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                (hashed_password, admin['id'])
            )
            
            print(f"✅ Password updated successfully for {admin['username']}!")
            print(f"\nYou can now log in with:")
            print(f"  Email: {admin['email']}")
            print(f"  Password: [the one you just entered]")
            return True
            
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = reset_admin_password()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nAborted by user")
        sys.exit(1)

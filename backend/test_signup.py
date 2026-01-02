"""
Test script to diagnose signup password hash issue.
This will test the entire signup flow without the API layer.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Try to load .env file if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")
    pass

from auth import get_password_hash, verify_password
from database_models import UserOperations
import mysql.connector
from database import get_db_cursor

def test_password_hash():
    """Test password hashing in isolation"""
    print("="*80)
    print("TEST 1: Password Hashing")
    print("="*80)
    
    test_password = "TestPassword123!"
    print(f"Test password: {test_password}")
    print(f"Password length: {len(test_password)} characters")
    print(f"Password bytes: {len(test_password.encode('utf-8'))} bytes")
    
    try:
        print("\nGenerating hash...")
        password_hash = get_password_hash(test_password)
        print(f"✅ Hash generated successfully!")
        print(f"Hash: {password_hash}")
        print(f"Hash length: {len(password_hash)} characters")
        print(f"Hash type: {type(password_hash)}")
        
        # Verify the hash works
        print("\nVerifying hash...")
        is_valid = verify_password(test_password, password_hash)
        print(f"✅ Verification: {'PASSED' if is_valid else 'FAILED'}")
        
        return password_hash
    except Exception as e:
        print(f"❌ ERROR during hashing: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_database_insert(password_hash):
    """Test inserting the hash into database"""
    print("\n" + "="*80)
    print("TEST 2: Database Insert")
    print("="*80)
    
    test_email = "test_user_12345@example.com"
    test_username = "testuser12345"
    
    try:
        # Clean up any previous test user
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM users WHERE email = %s", (test_email,))
            print(f"Cleaned up previous test user (if any)")
        
        print(f"\nAttempting to insert user...")
        print(f"Email: {test_email}")
        print(f"Username: {test_username}")
        print(f"Password hash length: {len(password_hash)} chars")
        
        # Try direct database insert
        with get_db_cursor(commit=True) as cursor:
            query = "INSERT INTO users (email, username, password_hash) VALUES (%s, %s, %s)"
            cursor.execute(query, (test_email, test_username, password_hash))
            user_id = cursor.lastrowid
            print(f"✅ User created successfully! ID: {user_id}")
        
        # Verify the data was stored correctly
        print("\nVerifying stored data...")
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, email, username, password_hash, LENGTH(password_hash) as hash_len FROM users WHERE email = %s", (test_email,))
            result = cursor.fetchone()
            
            if result:
                stored_id, stored_email, stored_username, stored_hash, stored_hash_len = result
                print(f"✅ User retrieved from database")
                print(f"   ID: {stored_id}")
                print(f"   Email: {stored_email}")
                print(f"   Username: {stored_username}")
                print(f"   Hash length: {stored_hash_len} chars")
                print(f"   Hash matches: {stored_hash == password_hash}")
                
                # Test authentication
                print("\nTesting authentication...")
                is_valid = verify_password("TestPassword123!", stored_hash)
                print(f"   Password verification: {'✅ PASSED' if is_valid else '❌ FAILED'}")
            else:
                print("❌ Could not retrieve user from database")
        
        # Clean up
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM users WHERE email = %s", (test_email,))
            print(f"\n🧹 Cleaned up test user")
            
    except mysql.connector.Error as e:
        print(f"\n❌ DATABASE ERROR: {e}")
        print(f"   Error code: {e.errno}")
        print(f"   SQL state: {e.sqlstate}")
        print(f"   Error message: {e.msg}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_user_operations():
    """Test the UserOperations.create method"""
    print("\n" + "="*80)
    print("TEST 3: UserOperations.create()")
    print("="*80)
    
    test_email = "test_ops_12345@example.com"
    test_username = "testops12345"
    test_password = "TestPassword123!"
    
    try:
        # Clean up first
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM users WHERE email = %s", (test_email,))
        
        print(f"Creating user via UserOperations.create()...")
        print(f"Email: {test_email}")
        print(f"Username: {test_username}")
        print(f"Password: {test_password}")
        
        user = UserOperations.create(
            email=test_email,
            username=test_username,
            password=test_password
        )
        
        if user:
            print(f"✅ User created successfully!")
            print(f"   ID: {user['id']}")
            print(f"   Email: {user['email']}")
            print(f"   Username: {user['username']}")
            
            # Verify authentication
            print("\nTesting authentication...")
            db_user = UserOperations.get_by_email(test_email)
            if db_user:
                is_valid = verify_password(test_password, db_user['password_hash'])
                print(f"   Password verification: {'✅ PASSED' if is_valid else '❌ FAILED'}")
            
            # Clean up
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("DELETE FROM users WHERE email = %s", (test_email,))
                print(f"\n🧹 Cleaned up test user")
        else:
            print("❌ UserOperations.create() returned None")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🔍 SIGNUP DIAGNOSTIC TEST")
    print("="*80)
    print("This will test the complete signup flow to identify the issue.\n")
    
    # Test 1: Hash generation
    password_hash = test_password_hash()
    
    if password_hash:
        # Test 2: Direct database insert
        test_database_insert(password_hash)
    
    # Test 3: Full UserOperations flow
    test_user_operations()
    
    print("\n" + "="*80)
    print("✅ DIAGNOSTIC COMPLETE")
    print("="*80)
    print("\nIf all tests passed, the issue might be:")
    print("  1. Frontend sending incorrect data")
    print("  2. API validation rejecting the request")
    print("  3. Network/CORS issues")
    print("\nIf tests failed, check the error messages above.")

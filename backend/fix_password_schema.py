"""
Database Schema Fix for Password Hash Field

This script checks and fixes the password_hash field in the users table to ensure
it can properly store bcrypt hashes (60 characters).

Run this script to diagnose and fix password hash truncation errors.
"""

import mysql.connector
import os
import sys
import re
from typing import Any

# Try to load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def check_and_fix_schema():
    """Check current schema and fix if needed"""
    try:
        # Connect to database
        print("Connecting to database...")
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "edusmart")
        )
        cursor = conn.cursor()
        print("✅ Connected successfully!\n")
        
        # Check current schema
        print("Checking current users table schema...")
        cursor.execute("DESCRIBE users;")
        columns = cursor.fetchall()
        
        print("\nCurrent schema:")
        print("-" * 80)
        print(f"{'Field':<20} {'Type':<20} {'Null':<10} {'Key':<10} {'Default':<15}")
        print("-" * 80)
        for col in columns:
            field, col_type, null, key, default, *_ = col
            null_str = null if null else "NO"
            key_str = key if key else ""
            default_str = str(default) if default else ""
            print(f"{field:<20} {col_type:<20} {null_str:<10} {key_str:<10} {default_str:<15}")
        print("-" * 80)
        
        # Find password_hash column
        # Type ignore because MySQL rows are accessed by index but type checker sees dict
        password_hash_col = [col for col in columns if str(col[0]) == 'password_hash']  # type: ignore
        if password_hash_col:
            current_type = str(password_hash_col[0][1])  # type: ignore
            print(f"\n📋 Current password_hash type: {current_type}")
            
            # Extract VARCHAR size if present
            if 'varchar' in current_type.lower():
                match = re.search(r'varchar\((\d+)\)', current_type, re.IGNORECASE)
                if match:
                    current_size = int(match.group(1))
                    print(f"   Current size: {current_size} characters")
                    
                    if current_size < 60:
                        print(f"\n❌ ERROR: VARCHAR({current_size}) is TOO SMALL for bcrypt hashes!")
                        print("   Bcrypt hashes are 60 characters long.")
                        print("   This is why you're getting truncation errors!")
                        fix_required = True
                    elif current_size < 255:
                        print(f"\n⚠️  VARCHAR({current_size}) works but not optimal.")
                        print("   Recommended: VARCHAR(255) for future compatibility.")
                        fix_required = True
                    else:
                        print(f"\n✅ VARCHAR({current_size}) is sufficient!")
                        fix_required = False
                else:
                    fix_required = True
            else:
                print(f"\n❌ ERROR: password_hash is not VARCHAR type!")
                fix_required = True
            
            # Apply fix if needed
            if fix_required:
                response = input("\n🔧 Do you want to fix this now? (yes/no): ").strip().lower()
                if response in ['yes', 'y']:
                    print("\nApplying fix...")
                    cursor.execute("""
                        ALTER TABLE users 
                        MODIFY COLUMN password_hash VARCHAR(255) NOT NULL;
                    """)
                    conn.commit()
                    print("✅ Schema updated successfully to VARCHAR(255)!")
                    
                    # Verify the change
                    cursor.execute("DESCRIBE users;")
                    columns_after = cursor.fetchall()
                    password_hash_col_after = [col for col in columns_after if str(col[0]) == 'password_hash']  # type: ignore
                    print(f"   New type: {str(password_hash_col_after[0][1])}")  # type: ignore
                else:
                    print("\n⏭️  Skipping fix. You can run this script again to apply the fix.")
                    print("\n   Manual fix SQL:")
                    print("   ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255) NOT NULL;")
        else:
            print("\n❌ ERROR: password_hash column not found!")
            print("   The users table may not have been created properly.")
            return
        
        # Test bcrypt hash generation
        print("\n" + "="*80)
        print("Testing bcrypt hash generation...")
        print("="*80)
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Test with various password lengths
        test_cases = [
            ("short", "Short1!"),
            ("medium", "MediumPassword123!"),
            ("long", "VeryLongPasswordWithLotsOfCharacters123456789!@#$%"),
            ("max_length", "x" * 100)  # Max from your validation
        ]
        
        print("\nTesting different password lengths:")
        for name, test_password in test_cases:
            # Truncate to 72 bytes as per bcrypt limit
            password_bytes = test_password.encode('utf-8')[:72]
            test_hash = pwd_context.hash(password_bytes)
            hash_length = len(test_hash)
            
            print(f"\n  {name} ({len(test_password)} chars):")
            print(f"    Password: {test_password[:50]}{'...' if len(test_password) > 50 else ''}")
            print(f"    Hash length: {hash_length} characters")
            print(f"    Hash: {test_hash[:30]}...{test_hash[-10:]}")
            print(f"    Fits in VARCHAR(255): {'✅' if hash_length <= 255 else '❌'}")
        
        # Check existing hashes in database
        print("\n" + "="*80)
        print("Checking existing password hashes in database...")
        print("="*80)
        cursor.execute("SELECT id, username, email, LENGTH(password_hash) as hash_length FROM users LIMIT 5")
        existing_users = cursor.fetchall()
        
        if existing_users:
            print(f"\nFound {len(existing_users)} user(s):")
            for user in existing_users:
                user_id, username, email, hash_length = user
                print(f"  ID {user_id}: {username} ({email}) - hash length: {hash_length} chars")
        else:
            print("\n  No users found in database yet.")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✅ Diagnostic complete!")
        print("="*80)
        
    except mysql.connector.Error as e:
        print(f"\n❌ Database error: {e}")
        print(f"   Error code: {e.errno}")
        print(f"   SQL state: {e.sqlstate if hasattr(e, 'sqlstate') else 'N/A'}")
        print(f"\n   Common causes:")
        print("   - Database connection details in .env are incorrect")
        print("   - Database server is not running")
        print("   - User doesn't have ALTER TABLE permissions")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("="*80)
    print("🔍 Password Hash Schema Diagnostic & Fix Tool")
    print("="*80)
    print("\nThis tool will:")
    print("  1. Check your current users table schema")
    print("  2. Identify if password_hash field is too small")
    print("  3. Offer to fix the schema automatically")
    print("  4. Test bcrypt hash generation")
    print("  5. Check existing hashes in your database")
    print("\n" + "="*80 + "\n")
    
    check_and_fix_schema()

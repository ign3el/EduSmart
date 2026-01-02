"""
Database migration: Add last_verification_sent column to users table
Run this script once to update existing databases
"""
import mysql.connector
import os

# Database connection from environment
MYSQL_HOST = os.getenv("MYSQL_HOST", "10.0.0.147")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "edusmart_db")

def add_last_verification_sent_column():
    """Add last_verification_sent column if it doesn't exist"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()
        
        print(f"Connected to database: {MYSQL_DATABASE}")
        
        # Check if column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'last_verification_sent'
        """, (MYSQL_DATABASE,))
        
        result = cursor.fetchone()
        exists = result[0] > 0 if result else False  # type: ignore
        
        if exists:
            print("✅ Column 'last_verification_sent' already exists!")
        else:
            print("Adding 'last_verification_sent' column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN last_verification_sent TIMESTAMP NULL 
                AFTER is_premium
            """)
            conn.commit()
            print("✅ Column 'last_verification_sent' added successfully!")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        return False
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("Database Migration: Add last_verification_sent column")
    print("="*60)
    add_last_verification_sent_column()

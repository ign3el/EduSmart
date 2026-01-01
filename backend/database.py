"""
Database connection and utilities for MySQL
"""
import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration from environment variables
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "10.0.0.147"),
    "user": os.getenv("MYSQL_USER", "root"),  # Default to root if not set
    "password": os.getenv("MYSQL_PASSWORD", ""),  # Default to empty password if not set
    "database": os.getenv("MYSQL_DATABASE", "edusmart_db"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "pool_name": "edusmart_pool",
    "pool_size": 5,
    "pool_reset_session": True,
    "autocommit": False
}

# Create connection pool
connection_pool = None
try:
    connection_pool = pooling.MySQLConnectionPool(**DB_CONFIG)
    print(f"✓ MySQL connection pool created successfully to {DB_CONFIG['host']}")
except Exception as e:
    print(f"⚠ Failed to create MySQL connection pool: {e}")
    print(f"   Ensure these environment variables are set:")
    print(f"   - MYSQL_HOST (currently: {DB_CONFIG['host']})")
    print(f"   - MYSQL_USER (currently: {DB_CONFIG['user']})")
    print(f"   - MYSQL_PASSWORD (currently: {'*' * len(DB_CONFIG['password']) if DB_CONFIG['password'] else 'NOT SET'})")
    print(f"   - MYSQL_DATABASE (currently: {DB_CONFIG['database']})")
    connection_pool = None


@contextmanager
def get_db_connection():
    """Context manager for database connections with automatic cleanup"""
    if not connection_pool:
        raise Exception("Database connection pool not initialized")
    
    conn = None
    try:
        conn = connection_pool.get_connection()
        yield conn
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn and conn.is_connected():
            conn.close()


@contextmanager
def get_db_cursor(dictionary=True):
    """Context manager for database cursor with automatic commit/rollback"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()


def init_database():
    """Initialize database tables - called on first API request"""
    if not connection_pool:
        print("⚠ Database not connected yet. Skipping table initialization.")
        return False
    
    try:
        with get_db_cursor() as cursor:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_verified BOOLEAN DEFAULT FALSE,
                    is_premium BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_email (email),
                    INDEX idx_username (username)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Email verifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_verifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_token (token),
                    INDEX idx_user_id (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # User stories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_stories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    story_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    story_data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_story_id (story_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            print("✓ Database tables initialized successfully")
            return True
    except Exception as e:
        print(f"⚠ Error initializing database: {e}")
        return False


# Flag to track if database has been initialized
_db_initialized = False

def ensure_db_initialized():
    """Ensure database is initialized (called on first API request)"""
    global _db_initialized
    if not _db_initialized:
        _db_initialized = init_database()
        return _db_initialized
    return True


# Try to initialize database on module import (best effort)
if connection_pool:
    try:
        init_database()
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")

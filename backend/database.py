"""
Database connection and utilities for MySQL
"""
import os
import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- Database Configuration ---
# Use os.getenv to read from environment, which is populated by Docker Compose
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "pool_name": "edusmart_pool",
    "pool_size": 5,
}

connection_pool = None

def get_connection_pool():
    """Initializes and returns the connection pool singleton."""
    global connection_pool
    if connection_pool is None:
        try:
            # Ensure all required config values are present
            for key in ["host", "user", "password", "database"]:
                if DB_CONFIG.get(key) is None:
                    raise ValueError(f"Missing required DB config: {key}")
            
            connection_pool = pooling.MySQLConnectionPool(**DB_CONFIG)
            logger.info(f"✓ MySQL connection pool created successfully to {DB_CONFIG['host']}")
        except (mysql.connector.Error, ValueError) as err:
            logger.error(f"⚠ Failed to create MySQL connection pool: {err}")
            # Log details without showing password
            config_details = {k: v for k, v in DB_CONFIG.items() if k != 'password'}
            logger.error(f"   Using config: {config_details}")
            # Set pool to None so subsequent calls don't succeed
            connection_pool = None
            raise
    return connection_pool

@contextmanager
def get_db_cursor(commit=False):
    """
    Provides a database cursor from the connection pool.
    Handles connection acquisition, cursor creation, and commit/rollback.
    """
    pool = get_connection_pool()
    if pool is None:
        raise ConnectionError("Database connection pool is not available.")
        
    connection = None
    cursor = None
    try:
        connection = pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        yield cursor
        if commit:
            connection.commit()
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        logger.error(f"Database Error: {err}")
        raise  # Re-raise the exception to be handled by the caller
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

# --- Schema Definition ---
TABLES = {}

TABLES['users'] = """
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
"""

TABLES['email_verifications'] = """
    CREATE TABLE IF NOT EXISTS email_verifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        token VARCHAR(255) UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_token (token)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

TABLES['user_stories'] = """
    CREATE TABLE IF NOT EXISTS user_stories (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        story_id VARCHAR(255) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        story_data JSON NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

def initialize_database():
    """Creates all tables defined in the TABLES dictionary."""
    try:
        # Commit=True because we are executing DDL (Data Definition Language)
        with get_db_cursor(commit=True) as cursor:
            logger.info("Initializing database schema...")
            for table_name, table_description in TABLES.items():
                logger.info(f"Creating table '{table_name}'...")
                cursor.execute(table_description)
            logger.info("✓ Database schema initialized successfully")
    except (mysql.connector.Error, ConnectionError) as err:
        logger.error(f"⚠ Could not initialize database: {err}")
        # This is a critical failure on startup, so re-raise
        raise
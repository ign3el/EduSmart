import os
import sys
from dotenv import load_dotenv
import mysql.connector

# Load env from current directory
load_dotenv()

config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "edusmart"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
}

print(f"Connecting to {config['host']} as {config['user']}...")
print(f"Database: {config['database']}")

try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, username, email, is_verified, is_admin, password_hash FROM users")
    users = cursor.fetchall()
    
    print(f"\n--- USER TABLE DUMP ({len(users)} users) ---")
    if not users:
        print(">> TABLE IS EMPTY <<")
        
    for u in users:
        ph = u['password_hash']
        short_hash = ph[:10] + "..." if ph else "NONE"
        print(f"ID: {u['id']:<3} | User: {u['username']:<15} | Email: {u['email']:<25} | Ver: {str(u['is_verified']):<5} | Hash: {short_hash}")
    print("-------------------------------------------\n")

except Exception as e:
    print(f"CRITICAL DB ERROR: {e}")

# Password Hash Truncation Error - Diagnostic & Fix

## Problem
You're seeing an error about "truncate password hash" when users try to sign up. This typically means the `password_hash` column in your database is too small to store bcrypt hashes.

## Root Cause
Bcrypt hashes are **60 characters long**. If your database column is smaller (e.g., VARCHAR(50)), MySQL will truncate the hash, causing authentication to fail.

## Quick Fix

### Option 1: Run the Diagnostic Script (Recommended)
```bash
cd backend
python fix_password_schema.py
```

This script will:
- ✅ Check your current database schema
- ✅ Show the exact size of your password_hash field
- ✅ Test bcrypt hash generation
- ✅ Offer to fix the issue automatically
- ✅ Verify the fix was applied

### Option 2: Manual SQL Fix
If you prefer to fix it manually, run this SQL command:

```sql
ALTER TABLE users 
MODIFY COLUMN password_hash VARCHAR(255) NOT NULL;
```

## How to Run the Diagnostic Script

1. **Make sure your database is running**
2. **Ensure your `.env` file has correct database credentials:**
   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=edusmart
   ```

3. **Run the script:**
   ```bash
   cd backend
   python fix_password_schema.py
   ```

4. **Follow the prompts** - The script will ask if you want to apply the fix

## What the Script Checks

### 1. Current Schema
Shows the exact definition of all columns in the `users` table, focusing on `password_hash`.

### 2. VARCHAR Size
- ❌ **VARCHAR(50) or less** - Too small, WILL cause truncation errors
- ⚠️ **VARCHAR(60-254)** - Works but not recommended
- ✅ **VARCHAR(255)** - Recommended for bcrypt hashes

### 3. Bcrypt Hash Testing
Tests actual bcrypt hash generation with different password lengths to verify they fit in your database.

### 4. Existing Data
Checks if you have existing users and shows their password hash lengths.

## Expected Output

### If Your Schema is Broken:
```
📋 Current password_hash type: varchar(50)
   Current size: 50 characters

❌ ERROR: VARCHAR(50) is TOO SMALL for bcrypt hashes!
   Bcrypt hashes are 60 characters long.
   This is why you're getting truncation errors!

🔧 Do you want to fix this now? (yes/no): 
```

### If Your Schema is Correct:
```
📋 Current password_hash type: varchar(255)
   Current size: 255 characters

✅ VARCHAR(255) is sufficient!
```

## After Fixing

1. **Restart your backend** (if it's running)
2. **Try signing up again** - It should work now!
3. **Existing users with truncated hashes** will need to reset their passwords

## Understanding Bcrypt

- **Hash Length**: Always 60 characters
- **Format**: `$2b$12$` (algorithm) + salt (22 chars) + hash (31 chars)
- **Example**: `$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY0K7xZRPIvpRCS`

## Troubleshooting

### "Can't connect to database"
- Check if MySQL/MariaDB is running
- Verify `.env` database credentials
- Check if database `edusmart` exists

### "Permission denied"
- Your database user needs `ALTER TABLE` permission
- Use root user or a user with admin privileges

### "Password hash column not found"
- The `users` table might not exist yet
- Run your backend once to create tables: `python main.py`

## Prevention

The issue occurs when:
1. You manually created the table with wrong schema
2. An old migration script ran with incorrect VARCHAR size
3. Database initialization used outdated schema

**Solution**: Always use the schema in `backend/database.py` which defines:
```python
password_hash VARCHAR(255) NOT NULL
```

## Technical Details

### Why 72 bytes?
Bcrypt has a hard limit of 72 bytes for input passwords. Our code correctly handles this in `auth.py`:

```python
def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    truncated_bytes = password_bytes[:72]  # Bcrypt limit
    return pwd_context.hash(truncated_bytes)  # Returns 60-char hash
```

### Why VARCHAR(255)?
- Bcrypt hashes are 60 chars
- VARCHAR(255) provides headroom for:
  - Future algorithm changes
  - Different bcrypt implementations
  - Migration to other hash algorithms (e.g., Argon2)

"""
Migration script to scan saved_stories folder and create database entries
for stories that exist on disk but not in the database.
"""
import os
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_models import StoryOperations
from database import get_db_cursor
import mysql.connector

def scan_and_migrate_stories():
    """Scan saved_stories folder and create DB entries for orphaned stories."""
    
    # Try multiple possible locations
    possible_paths = [
        Path("saved_stories"),
        Path("backend/saved_stories"),
        Path("/app/saved_stories"),  # Docker container path
        Path("/app/backend/saved_stories")
    ]
    
    saved_stories_path = None
    for path in possible_paths:
        if path.exists():
            saved_stories_path = path
            break
    
    if not saved_stories_path:
        print("❌ saved_stories folder not found in any expected location:")
        for path in possible_paths:
            print(f"   - {path.absolute()}")
        return
    
    print(f"📁 Scanning {saved_stories_path}...")
    
    story_folders = [f for f in saved_stories_path.iterdir() if f.is_dir()]
    print(f"Found {len(story_folders)} story folders\n")
    
    # Get admin user ID
    admin_user_id = None
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE is_admin = 1 LIMIT 1")
            admin = cursor.fetchone()
            if admin:
                admin_user_id = admin['id']
                print(f"✓ Found admin user (ID: {admin_user_id}) - will assign orphaned stories to admin\n")
            else:
                print("⚠️  No admin user found - stories will fail to migrate\n")
                return
    except Exception as e:
        print(f"❌ Failed to get admin user: {e}\n")
        return
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    for story_folder in story_folders:
        folder_name = story_folder.name
        metadata_path = story_folder / "metadata.json"
        
        if not metadata_path.exists():
            print(f"⚠️  {folder_name}: No metadata.json found, skipping")
            skipped_count += 1
            continue
        
        # Check if story already exists in database
        try:
            # Read metadata.json
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            story_id = metadata.get('id', folder_name)
            story_name = metadata.get('name', 'Untitled Story')
            story_data = metadata.get('story_data', {})
            story_title = story_data.get('title', story_name)
            
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("SELECT story_id FROM user_stories WHERE story_id = %s", (story_id,))
                existing = cursor.fetchone()
                
                if existing:
                    print(f"✓ {story_id}: Already in database, skipping")
                    skipped_count += 1
                    continue
                
                # Insert into database assigned to admin
                query = """
                    INSERT INTO user_stories (story_id, user_id, name, story_data, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                now = datetime.now()
                # Try to get creation time from folder
                created_at = datetime.fromtimestamp(story_folder.stat().st_ctime)
                
                cursor.execute(query, (
                    story_id,
                    admin_user_id,  # Assign to admin instead of NULL
                    story_name,
                    json.dumps(story_data),
                    created_at,
                    now
                ))
                
                print(f"✅ {story_id}: Migrated '{story_name}'")
                migrated_count += 1
                
        except mysql.connector.Error as e:
            print(f"❌ {story_id}: Database error - {e}")
            error_count += 1
        except json.JSONDecodeError as e:
            print(f"❌ {story_id}: Invalid JSON - {e}")
            error_count += 1
        except Exception as e:
            print(f"❌ {story_id}: Error - {e}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Migration Complete!")
    print(f"{'='*60}")
    print(f"✅ Migrated: {migrated_count}")
    print(f"⏭️  Skipped:  {skipped_count}")
    print(f"❌ Errors:   {error_count}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    print("="*60)
    print("EduSmart - Saved Stories Database Migration")
    print("="*60)
    print("This script will scan the saved_stories folder and create")
    print("database entries for stories that are missing from the DB.\n")
    
    try:
        scan_and_migrate_stories()
        print("✓ Migration script completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""
Repair existing stories by copying their assets from outputs to saved_stories
"""
import os
import shutil
import json
from database import get_db_cursor
from datetime import datetime

def repair_story(story_id):
    print(f"\n=== Repairing Story: {story_id} ===\n")
    
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("SELECT * FROM user_stories WHERE story_id = %s", (story_id,))
            story = cursor.fetchone()
            
            if not story:
                print(f"❌ Story not found")
                return False
            
            print(f"✓ Found story: {story['name']}")
            
            story_data = story.get('story_data')
            if isinstance(story_data, str):
                story_data = json.loads(story_data)
            
            # Create story directory if it doesn't exist
            story_dir = os.path.join("saved_stories", story_id)
            os.makedirs(story_dir, exist_ok=True)
            print(f"✓ Created directory: {story_dir}")
            
            scenes = story_data.get('scenes', [])
            print(f"📊 Processing {len(scenes)} scenes...")
            
            updated = False
            for i, scene in enumerate(scenes):
                # Process image
                if scene.get('image_url') and scene['image_url'].startswith('/api/outputs/'):
                    old_path = scene['image_url'].replace('/api/outputs/', 'outputs/')
                    if os.path.exists(old_path):
                        filename = os.path.basename(old_path)
                        new_path = os.path.join(story_dir, filename)
                        shutil.copy2(old_path, new_path)
                        scene['image_url'] = f'/api/saved-stories/{story_id}/{filename}'
                        updated = True
                        print(f"  ✓ Scene {i} image: {filename}")
                    else:
                        print(f"  ⚠️  Scene {i} image not found: {old_path}")
                
                # Process audio
                if scene.get('audio_url') and scene['audio_url'].startswith('/api/outputs/'):
                    old_path = scene['audio_url'].replace('/api/outputs/', 'outputs/')
                    if os.path.exists(old_path):
                        filename = os.path.basename(old_path)
                        new_path = os.path.join(story_dir, filename)
                        shutil.copy2(old_path, new_path)
                        scene['audio_url'] = f'/api/saved-stories/{story_id}/{filename}'
                        updated = True
                        print(f"  ✓ Scene {i} audio: {filename}")
                    else:
                        print(f"  ⚠️  Scene {i} audio not found: {old_path}")
            
            if updated:
                # Update database with new URLs
                cursor.execute(
                    "UPDATE user_stories SET story_data = %s, updated_at = %s WHERE story_id = %s",
                    (json.dumps(story_data), datetime.now(), story_id)
                )
                print(f"\n✅ Story repaired and database updated!")
                return True
            else:
                print(f"\n⚠️  No files found in outputs to copy")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python repair_story.py <story_id>")
        sys.exit(1)
    
    repair_story(sys.argv[1])

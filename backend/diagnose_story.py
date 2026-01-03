"""
Diagnose story asset issues
"""
import json
from database_models import StoryOperations
from database import get_db_cursor

def diagnose_story(story_id):
    print(f"\n=== Diagnosing Story: {story_id} ===\n")
    
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM user_stories WHERE story_id = %s", (story_id,))
            story = cursor.fetchone()
            
            if not story:
                print(f"❌ Story not found in database")
                return
            
            print(f"✓ Story found in database:")
            print(f"  - ID: {story['story_id']}")
            print(f"  - Name: {story['name']}")
            print(f"  - User ID: {story['user_id']}")
            print(f"  - Created: {story['created_at']}")
            
            story_data = story.get('story_data')
            if isinstance(story_data, str):
                story_data = json.loads(story_data)
            
            print(f"\n📊 Story Data:")
            print(f"  - Title: {story_data.get('title', 'N/A')}")
            print(f"  - Scenes: {len(story_data.get('scenes', []))}")
            print(f"  - Quiz: {len(story_data.get('quiz', []))} questions")
            
            print(f"\n🖼️ Asset URLs (first 3 scenes):")
            for i, scene in enumerate(story_data.get('scenes', [])[:3]):
                print(f"\nScene {i}:")
                print(f"  - Image: {scene.get('image_url', 'N/A')}")
                print(f"  - Audio: {scene.get('audio_url', 'N/A')}")
                print(f"  - Text: {scene.get('text', 'N/A')[:50]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python diagnose_story.py <story_id>")
        sys.exit(1)
    
    diagnose_story(sys.argv[1])

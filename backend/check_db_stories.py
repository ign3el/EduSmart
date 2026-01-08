from database_models import StoryOperations

stories = StoryOperations.get_all_stories()
print(f"Total stories in database: {len(stories)}")
print("\nFirst 5 stories:")
for i, story in enumerate(stories[:5], 1):
    print(f"\n{i}. ID: {story['id']}")
    print(f"   Title: {story.get('title', 'N/A')}")
    print(f"   Created: {story.get('created_at', 'N/A')}")
    print(f"   User: {story.get('username', 'N/A')}")

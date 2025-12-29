import os
from google import genai
from dotenv import load_dotenv

# Load .env from the backend folder
load_dotenv("backend/.env")

# FIX: Use the variable name you actually have in your file
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found. Check your .env file.")
else:
    print(f"✅ Key found: {api_key[:5]}...")
    try:
        client = genai.Client(api_key=api_key)
        print("\n🔍 RAW MODEL LIST (Pick one of these):")
        print("----------------------------------------")
        
        # Simple loop - print every model name available
        for m in client.models.list():
            print(f"👉 {m.name}")
            
        print("----------------------------------------")
    except Exception as e:
        print(f"❌ Error: {e}")
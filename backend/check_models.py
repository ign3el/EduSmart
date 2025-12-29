import os
from google import genai
from dotenv import load_dotenv

# Load your API key
load_dotenv("backend/.env")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env")
else:
    print(f"✅ Found API Key: {api_key[:5]}...")
    try:
        # Initialize Client
        client = genai.Client(api_key=api_key)
        
        print("\n🔍 Listing available models for this key:")
        print("----------------------------------------")
        
        # CORRECT SYNTAX for new SDK:
        for m in client.models.list():
            # Check if it supports content generation
            if "generateContent" in (m.supported_generation_methods or []):
                # The model name usually comes like 'models/gemini-1.5-flash'
                print(f"👉 {m.name}")
        
        print("\n----------------------------------------")
            
    except Exception as e:
        print(f"\n❌ API Error: {e}")
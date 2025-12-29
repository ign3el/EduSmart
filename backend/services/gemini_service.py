import os
import json
import random
import time
import requests
from google import genai
from google.genai import types
import docx
import pptx

class GeminiService:
    def __init__(self):
        # 1. Load API Key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("CRITICAL WARNING: GEMINI_API_KEY is missing!")
        
        self.client = genai.Client(api_key=api_key)
        
        # 2. Text Model (This works for everyone)
        self.text_model = "gemini-2.5-flash"

    def process_file_to_story(self, file_path: str):
        """Reads file and generates story structure."""
        ext = os.path.splitext(file_path)[1].lower()
        content_part = None
        
        # File Processing
        if ext == ".pdf":
            with open(file_path, "rb") as f:
                pdf_data = f.read()
            content_part = types.Part.from_bytes(data=pdf_data, mime_type="application/pdf")
        elif ext == ".docx":
            try:
                doc = docx.Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
                content_part = f"Word Doc Content:\n{text}"
            except: return None
        elif ext == ".pptx":
            try:
                prs = pptx.Presentation(file_path)
                text = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            text.append(shape.text)
                content_part = f"PowerPoint Content:\n" + "\n".join(text)
            except: return None
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                content_part = f.read()

        if not content_part:
            return None

        # Generate Story JSON
        try:
            time.sleep(1) # Safety pause
            
            prompt = """
            You are a game designer converting this content into an Interactive Visual Novel for kids (Age 6-8).
            Create a linear story where the user learns the topic through a narrative.
            
            Return strictly valid JSON (no markdown) with this structure:
            {
              "title": "Story Title",
              "story_id": "unique_id_placeholder",
              "scenes": [
                {
                  "id": 1,
                  "text": "Story narration for this scene (engaging, max 2 sentences).",
                  "image_description": "Visual description for the artist, 3d pixar style",
                  "character_details": "Blue robot named Beep",
                  "interaction": {
                      "question": "A simple question about what just happened?",
                      "options": ["Option A", "Option B"],
                      "correct_answer": "Option A"
                  }
                }
              ]
            }
            """
            contents = [content_part, prompt]
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=contents,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Story Gen Error: {e}")
            return None

    def generate_image(self, prompt: str, seed: int = None):
        """Generates image using Pollinations.ai (Free, No Auth)."""
        try:
            # We use a URL-based free generation API
            # This bypasses Google's billing requirement
            clean_prompt = prompt.replace(" ", "%20")
            if seed:
                clean_prompt += f"&seed={seed}"
                
            image_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=576&nologo=true"
            
            # Fetch the image bytes
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            print(f"Image Gen Error: {e}")
            return None

    def generate_voiceover(self, text: str):
        """Placeholder for Audio (Google Audio is Billed-Only)."""
        # Returning None keeps the app fast and crash-free.
        # If you add a credit card later, we can re-enable Google Audio.
        return None
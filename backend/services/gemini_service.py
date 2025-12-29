import os
import json
import random
import time
import requests
import urllib.parse  # <--- NEW: For safe URL encoding
from google import genai
from google.genai import types
import docx
import pptx

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("CRITICAL WARNING: GEMINI_API_KEY is missing!")
        
        self.client = genai.Client(api_key=api_key)
        self.text_model = "gemini-2.5-flash"

    def process_file_to_story(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        content_part = None
        
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

        try:
            time.sleep(1)
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
        """Generates image with Smart Retry (High Quality -> Safe Mode)."""
        try:
            # 1. Clean the prompt safely
            clean_prompt = urllib.parse.quote(prompt)
            seed_param = f"&seed={seed}" if seed else ""
            
            # ATTEMPT 1: High Quality (Flux Model + Enhance)
            url_hq = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=576&model=flux&nologo=true&enhance=true{seed_param}"
            
            try:
                response = requests.get(url_hq, timeout=30)
                if response.status_code == 200:
                    return response.content
                else:
                    print(f"HQ Image Failed ({response.status_code}), retrying safe mode...")
            except:
                print("HQ Image Timeout, retrying safe mode...")

            # ATTEMPT 2: Safe Mode (Turbo Model + No Extra Params)
            # This is much faster and rarely crashes 500
            url_safe = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=576&model=turbo{seed_param}"
            
            response = requests.get(url_safe, timeout=30)
            if response.status_code == 200:
                return response.content
            
            print(f"All Image Attempts Failed: {response.status_code}")
            return None
            
        except Exception as e:
            print(f"Image Gen Critical Error: {e}")
            return None

    def generate_voiceover(self, text: str):
        return None
import os
import json
import base64
import re # Added for cleaning JSON strings
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = "gemini-2.0-flash-exp"
        self.audio_model = "gemini-2.0-flash-exp"

    def process_file_to_story(self, file_path, grade_level):
        """Analyzes PDF and returns a cleaned, structured JSON story."""
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            
        prompt = (
            f"Analyze this PDF and create a {grade_level} story with exactly 5 scenes. "
            "For each scene, provide 'text' and a detailed 'image_description'. "
            "Also include a 'quiz' array with 3 multiple-choice questions. "
            "Return the response ONLY as a JSON object."
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            # Clean response text in case AI added markdown formatting
            raw_text = response.text
            clean_json = re.sub(r'^```json\s*|\s*```$', '', raw_text.strip(), flags=re.MULTILINE)
            
            story_data = json.loads(clean_json)
            
            # Validation check
            if "scenes" not in story_data or not story_data["scenes"]:
                raise ValueError("Missing 'scenes' in AI response")
                
            return story_data

        except Exception as e:
            print(f"STORY GEN ERROR: {e}")
            return None

    def generate_image(self, prompt):
        try:
            response = self.client.models.generate_content(
                model="imagen-3.0-generate-001",
                contents=f"Educational cartoon style, high quality: {prompt}",
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            return response.candidates[0].content.parts[0].inline_data.data
        except Exception as e:
            print(f"Image Gen Error: {e}")
            return None

    def generate_voiceover(self, text):
        try:
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=text,
                config=types.GenerateContentConfig(response_modalities=["AUDIO"])
            )
            
            if response.candidates and response.candidates[0].content.parts:
                audio_part = response.candidates[0].content.parts[0].inline_data.data
                if isinstance(audio_part, str):
                    return base64.b64decode(audio_part)
                return audio_part
            return None
        except Exception as e:
            print(f"Audio Gen Error: {e}")
            return None
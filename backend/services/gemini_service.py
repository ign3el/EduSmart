import os
import json # Added this to fix the "json is not defined" error
import base64
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        # Ensure your API key is set in your environment or aaPanel
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = "gemini-2.0-flash-exp"
        self.audio_model = "gemini-2.0-flash-exp"

    def process_file_to_story(self, file_path, grade_level):
        """Analyzes PDF and returns a structured JSON story."""
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            
        prompt = (
            f"Analyze this PDF and create a {grade_level} story with 5-6 scenes. "
            "For each scene, provide 'text' and a detailed 'image_description'. "
            "Also include a 3-question quiz. Return strictly as JSON."
        )
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                prompt
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        # Pylance was complaining here because 'json' wasn't imported
        return json.loads(response.text)

    def generate_image(self, prompt):
        """Generates an illustration using Imagen 3."""
        try:
            response = self.client.models.generate_content(
                model="imagen-3.0-generate-001",
                contents=f"Educational cartoon style, child friendly: {prompt}",
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            return response.candidates[0].content.parts[0].inline_data.data
        except Exception as e:
            print(f"Image Gen Error: {e}")
            return None

    def generate_voiceover(self, text):
        """Generates audio and ensures it is returned as clean binary bytes."""
        try:
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=text,
                config=types.GenerateContentConfig(response_modalities=["AUDIO"])
            )
            
            if response.candidates and response.candidates[0].content.parts:
                audio_part = response.candidates[0].content.parts[0].inline_data.data
                
                # If the AI sends a string, it is Base64 and MUST be decoded
                if isinstance(audio_part, str):
                    return base64.b64decode(audio_part)
                
                return audio_part
            return None
        except Exception as e:
            print(f"Audio Gen Error: {e}")
            return None
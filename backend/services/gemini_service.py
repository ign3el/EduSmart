import os
import json
import base64
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Standard multimodal model
        self.model_name = "gemini-2.0-flash-exp" 

    def process_file_to_story(self, file_path, grade_level):
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        story_schema = {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING"},
                "scenes": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "text": {"type": "STRING"},
                            "image_description": {"type": "STRING"}
                        },
                        "required": ["text", "image_description"]
                    }
                },
                "quiz": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "question": {"type": "STRING"},
                            "options": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "answer": {"type": "STRING"}
                        },
                        "required": ["question", "options", "answer"]
                    }
                }
            },
            "required": ["title", "scenes", "quiz"]
        }

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                    f"Create a {grade_level} educational story based on this PDF."
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=story_schema
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Story Error: {e}")
            return None

    def generate_image(self, prompt):
        """FIX: Uses the dedicated generate_image method to avoid 404/400 errors."""
        try:
            # Imagen 3 MUST use the generate_image method
            response = self.client.models.generate_image(
                model="imagen-3.0-generate-001",
                prompt=f"Educational cartoon style illustration: {prompt}",
            )
            # generate_image returns 'image_bytes' in a different structure
            return response.generated_images[0].image_bytes
        except Exception as e:
            print(f"Image Gen Error: {e}")
            return None

    def generate_voiceover(self, text):
        """Uses generate_content with audio modality for native TTS."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"]
                )
            )
            if response.candidates and response.candidates[0].content.parts:
                audio_part = response.candidates[0].content.parts[0].inline_data.data
                # Binary decode to fix NotSupportedError
                return base64.b64decode(audio_part) if isinstance(audio_part, str) else audio_part
            return None
        except Exception as e:
            print(f"Audio Gen Error: {e}")
            return None
import os
import json
import base64
import re
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = "gemini-2.0-flash-exp"
        self.audio_model = "gemini-2.0-flash-exp"

    def process_file_to_story(self, file_path, grade_level):
        """Analyzes PDF using a strict JSON schema to prevent missing 'scenes' errors."""
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Define the exact structure the AI MUST follow
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

        prompt = (
            f"Act as an expert educator. Analyze this PDF about desert plants and create a {grade_level} "
            "educational story. Break it into 5-6 engaging scenes with narrations and image descriptions. "
            "Finally, add a 3-question quiz."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=story_schema # Forces the correct keys
                )
            )
            
            # response.text is guaranteed to follow the schema now
            return json.loads(response.text)

        except Exception as e:
            print(f"STORY GEN ERROR: {e}")
            return None

    def generate_image(self, prompt):
        try:
            response = self.client.models.generate_content(
                model="imagen-3.0-generate-001",
                contents=f"High quality educational illustration, cartoon style: {prompt}",
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
                return base64.b64decode(audio_part) if isinstance(audio_part, str) else audio_part
            return None
        except Exception as e:
            print(f"Audio Gen Error: {e}")
            return None
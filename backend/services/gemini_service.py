import os
import json
import base64
from pydantic import BaseModel
from typing import List
from google import genai
from google.genai import types

class QuizItem(BaseModel):
    question: str
    options: List[str]
    answer: str

class Scene(BaseModel):
    text: str
    image_description: str

class StorySchema(BaseModel):
    title: str
    scenes: List[Scene]
    quiz: List[QuizItem]

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Using the exact strings from your VPS list
        self.text_model = "gemini-3-flash-preview"
        self.audio_model = "gemini-2.5-flash-preview-tts"
        self.image_model = "gemini-3-pro-image-preview"

    def process_file_to_story(self, file_path, grade_level):
        print(f"DEBUG: Processing PDF at {file_path}")
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        try:
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                    f"Create a {grade_level} educational story as JSON."
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=StorySchema,
                )
            )
            print("DEBUG: Story text generated successfully.")
            return json.loads(response.text)
        except Exception as e:
            print(f"CRITICAL STORY ERROR: {e}")
            return None

    def generate_image(self, prompt):
        """Native multimodal image generation."""
        try:
            print(f"DEBUG: Starting image gen for: {prompt[:30]}...")
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=f"Educational cartoon: {prompt}",
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"IMAGE ERROR: {e}")
            return None

    def generate_voiceover(self, text):
        """Native TTS with strict Base64 to Binary conversion."""
        try:
            print(f"DEBUG: Starting audio gen for text length: {len(text)}")
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=text,
                config=types.GenerateContentConfig(response_modalities=["AUDIO"])
            )
            
            audio_part = response.candidates[0].content.parts[0].inline_data.data
            
            # If the data is a string, it MUST be decoded to binary bytes
            # Otherwise, it saves as a text file which causes 'NotSupportedError'
            if isinstance(audio_part, str):
                return base64.b64decode(audio_part)
            
            return audio_part
        except Exception as e:
            print(f"AUDIO ERROR: {e}")
            return None
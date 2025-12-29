import os
import json
import base64
import time # Added for sleep between retries
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
        self.text_model = "gemini-3-flash-preview"
        self.audio_model = "gemini-2.5-flash-preview-tts"
        self.image_model = "gemini-3-pro-image-preview"

    def process_file_to_story(self, file_path, grade_level):
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
            return json.loads(response.text)
        except Exception as e:
            print(f"STORY ERROR: {e}")
            return None

    def generate_image(self, prompt):
        try:
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=f"Educational cartoon: {prompt}",
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            return response.candidates[0].content.parts[0].inline_data.data
        except Exception as e:
            print(f"IMAGE ERROR: {e}")
            return None

    def generate_voiceover(self, text, retries=3):
        """Native TTS with automatic retry for 500 Internal Errors."""
        attempt = 0
        while attempt < retries:
            try:
                response = self.client.models.generate_content(
                    model=self.audio_model,
                    contents=text,
                    config=types.GenerateContentConfig(response_modalities=["AUDIO"])
                )
                
                audio_part = response.candidates[0].content.parts[0].inline_data.data
                
                # Critical: Return raw bytes to stop 'NotSupportedError'
                if isinstance(audio_part, str):
                    return base64.b64decode(audio_part)
                return audio_part

            except Exception as e:
                attempt += 1
                print(f"AUDIO ATTEMPT {attempt} FAILED: {e}")
                if attempt < retries:
                    time.sleep(2) # Wait 2 seconds before retrying
                else:
                    return None
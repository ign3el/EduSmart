import os
import json
import base64
from pydantic import BaseModel
from typing import List
from google import genai
from google.genai import types

# Define strict schemas to prevent "Empty Object" errors
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
        self.image_model = "imagen-3.0-generate-001"

    def process_file_to_story(self, file_path, grade_level):
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        prompt = f"Create a {grade_level} educational story with 5 scenes and a 3-question quiz from this PDF."

        try:
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=StorySchema,
                    thinking_config=types.ThinkingConfig(include_thoughts=True)
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Story Gen Error: {e}")
            return None

    def generate_image(self, prompt):
        """FIXED: Uses generate_images (plural) for the latest SDK."""
        try:
            response = self.client.models.generate_images(
                model=self.image_model,
                prompt=f"Child-friendly educational art: {prompt}",
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            # The bytes are in .image.image_bytes
            return response.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"Image Gen Error: {e}")
            return None

    def generate_voiceover(self, text):
        try:
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
                        )
                    )
                )
            )
            data = response.candidates[0].content.parts[0].inline_data.data
            return base64.b64decode(data) if isinstance(data, str) else data
        except Exception as e:
            print(f"Audio Gen Error: {e}")
            return None
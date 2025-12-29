import os
import json
import base64
from pydantic import BaseModel
from typing import List
from google import genai
from google.genai import types

# Define the structure for the quiz to avoid "empty object" errors
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
        # Optimized 2025 model selection from your VPS list
        self.text_model = "gemini-3-flash-preview"
        self.audio_model = "gemini-2.5-flash-preview-tts"
        self.image_model = "imagen-4.0-fast-generate-001"

    def process_file_to_story(self, file_path, grade_level):
        """Analyzes PDF and returns a structured story using Gemini 3."""
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        prompt = (
            f"Analyze this PDF and create a {grade_level} educational story. "
            "Provide 5 engaging scenes and a 3-question quiz."
        )

        try:
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    # Pass the Pydantic class to ensure strict JSON formatting
                    response_schema=StorySchema,
                    thinking_config=types.ThinkingConfig(include_thoughts=True)
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"STORY GEN ERROR: {e}")
            return None

    def generate_image(self, prompt):
        """Uses Imagen 4.0 via the dedicated generate_image method."""
        try:
            response = self.client.models.generate_image(
                model=self.image_model,
                prompt=f"Educational cartoon, high quality: {prompt}",
            )
            # The new SDK returns image_bytes directly in this method
            return response.generated_images[0].image_bytes
        except Exception as e:
            print(f"Image Gen Error: {e}")
            return None

    def generate_voiceover(self, text):
        """Generates high-fidelity native audio."""
        try:
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=f"Tell this story cheerfully: {text}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Aoede" 
                            )
                        )
                    )
                )
            )
            # Binary decode fix for browser compatibility
            data = response.candidates[0].content.parts[0].inline_data.data
            return base64.b64decode(data) if isinstance(data, str) else data
        except Exception as e:
            print(f"Audio Gen Error: {e}")
            return None
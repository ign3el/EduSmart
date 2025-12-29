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
        # Using Gemini 3 models from your previous terminal list
        self.text_model = "gemini-3-flash-preview"
        self.audio_model = "gemini-2.5-flash-preview-tts"
        # The multimodal image model
        self.image_model = "gemini-3-pro-image-preview" 

    def process_file_to_story(self, file_path, grade_level):
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        prompt = f"Analyze this PDF and create a {grade_level} story with 5 scenes and a 3-question quiz. Return JSON."
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
            print(f"Story Error: {e}")
            return None

    def generate_image(self, prompt):
        """
        Uses Gemini 3 multimodal generation.
        This fixes the 404 error by avoiding the 'predict' method.
        """
        try:
            # We call generate_content because this is a multimodal model
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=f"Generate a child-friendly educational illustration: {prompt}",
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"] # Tells Gemini to output an image
                )
            )
            
            # The image data is returned as an 'inline_data' part
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        # Success: return the raw bytes
                        return part.inline_data.data
            return None
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
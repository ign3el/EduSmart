import os
import json
import base64
import time
from pydantic import BaseModel
from typing import List, Optional, Any
from google import genai
from google.genai import types

# 1. RESPONSE SCHEMAS (Ensures strict JSON structure)
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
    def __init__(self) -> None:
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.text_model = "gemini-3-flash-preview"
        self.audio_model = "gemini-2.5-flash-preview-tts"
        self.image_model = "gemini-3-pro-image-preview"

    def process_file_to_story(self, file_path: str, grade_level: str) -> Optional[dict]:
        """Generates the story JSON structure."""
        print(f"DEBUG: Starting PDF analysis for {file_path}")
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                    f"Create a {grade_level} educational story with 5-6 scenes and a quiz as JSON."
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=StorySchema,
                )
            )
            
            # Pylance Fix: Check if response.text exists before parsing
            if response.text:
                print("SUCCESS: Story text and structure generated.")
                return json.loads(response.text)
            
            print("ERROR: AI returned an empty text response.")
            return None
        except Exception as e:
            print(f"STORY ERROR: {e}")
            return None

    def generate_image(self, prompt: str) -> Optional[bytes]:
        """Native multimodal image generation with safe type handling."""
        try:
            print(f"DEBUG: Generating image for: {prompt[:40]}...")
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=f"Educational cartoon illustration: {prompt}",
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            
            # Pylance Fix: Defensive checks for nested attributes
            if not (response.candidates and 
                    response.candidates[0].content and 
                    response.candidates[0].content.parts):
                return None

            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"IMAGE ERROR: {e}")
            return None

    def generate_voiceover(self, text: str, retries: int = 2) -> Optional[bytes]:
        """Native TTS with strict Base64 decoding and safe attribute access."""
        attempt = 0
        while attempt <= retries:
            try:
                print(f"DEBUG: Generating audio (Attempt {attempt+1})...")
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
                
                # Pylance Fix: Ensure candidates and parts exist
                if not (response.candidates and 
                        response.candidates[0].content and 
                        response.candidates[0].content.parts):
                    raise ValueError("Incomplete API response for audio")

                audio_part = response.candidates[0].content.parts[0]
                
                # Pylance Fix: Check for inline_data and data presence
                if audio_part.inline_data and audio_part.inline_data.data:
                    audio_data = audio_part.inline_data.data
                    
                    if isinstance(audio_data, str):
                        return base64.b64decode(audio_data)
                    return audio_data
                
                raise ValueError("No audio data found in response")

            except Exception as e:
                attempt += 1
                print(f"AUDIO ERROR on attempt {attempt}: {e}")
                if attempt <= retries:
                    time.sleep(2)
        return None
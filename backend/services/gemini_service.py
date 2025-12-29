import os
import json
import base64
import time
from typing import Optional, Any
from google import genai
from google.genai import types
from models import StorySchema

class GeminiService:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Using exact model names from your verified list
        self.text_model = "gemini-3-flash-preview"
        self.image_model = "gemini-3-pro-image-preview"
        self.audio_model = "gemini-2.5-flash" 

    def process_file_to_story(self, file_path: str, grade_level: str) -> Optional[dict]:
        """Generates the story JSON structure with safety checks."""
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
            
            # Safe access to text to satisfy Pylance
            if response.text:
                return json.loads(response.text)
            
            return None
        except Exception as e:
            print(f"STORY ERROR: {e}")
            return None

    def generate_image(self, prompt: str) -> Optional[bytes]:
        """Multimodal image generation with exhaustive attribute checking."""
        try:
            print(f"DEBUG: Generating image for: {prompt[:40]}...")
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=f"Educational cartoon illustration: {prompt}",
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            
            # Verify the response chain isn't None
            if not (response.candidates and 
                    response.candidates[0].content and 
                    response.candidates[0].content.parts):
                return None

            for part in response.candidates[0].content.parts:
                # FIX: Check both inline_data AND its data attribute
                if part.inline_data and part.inline_data.data:
                    return part.inline_data.data
            
            return None
        except Exception as e:
            print(f"IMAGE ERROR: {e}")
            return None

    def generate_voiceover(self, text: str, retries: int = 2) -> Optional[bytes]:
        """Native TTS with Base64-to-Binary decoding."""
        attempt = 0
        while attempt <= retries:
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
                
                # Nested safety check for audio parts
                if not (response.candidates and 
                        response.candidates[0].content and 
                        response.candidates[0].content.parts):
                    raise ValueError("Incomplete audio response structure")

                audio_part = response.candidates[0].content.parts[0]
                
                # FIXED: Pylance check for optional member access
                if audio_part.inline_data and audio_part.inline_data.data:
                    audio_data = audio_part.inline_data.data
                    
                    # Convert Base64 string to raw binary bytes for MP3
                    if isinstance(audio_data, str):
                        return base64.b64decode(audio_data)
                    return audio_data
                
                raise ValueError("No binary audio data found in response")

            except Exception as e:
                attempt += 1
                print(f"AUDIO ERROR (Attempt {attempt}): {e}")
                # Exponential backoff for rate limits
                if "429" in str(e):
                    time.sleep(10 * attempt) 
                else:
                    time.sleep(2)
        return None
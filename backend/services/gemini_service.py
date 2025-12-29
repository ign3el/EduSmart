import os
import json
import base64
import time
import random
from typing import Optional, Any
from google import genai
from google.genai import types
from models import StorySchema

class GeminiService:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.text_model = "gemini-3-flash-preview"
        self.image_model = "gemini-3-pro-image-preview"
        # SWITCHED TO LITE: Optimized for cost and availability
        self.audio_model = "gemini-1.5-flash " 

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
            
            if response.text:
                return json.loads(response.text)
            
            return None
        except Exception as e:
            print(f"STORY ERROR: {e}")
            return None

    def generate_image(self, prompt: str) -> Optional[bytes]:
        """Multimodal image generation."""
        try:
            print(f"DEBUG: Generating image for: {prompt[:40]}...")
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=f"Educational cartoon illustration: {prompt}",
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            
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

    def generate_voiceover(self, text: str, retries: int = 3) -> Optional[bytes]:
        """
        TTS with Exponential Backoff + Jitter for 429/500 errors.
        """
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
                
                # Validation checks
                if not (response.candidates and 
                        response.candidates[0].content and 
                        response.candidates[0].content.parts):
                    raise ValueError("Incomplete audio response structure")

                audio_part = response.candidates[0].content.parts[0]
                
                # Data extraction
                if audio_part.inline_data and audio_part.inline_data.data:
                    audio_data = audio_part.inline_data.data
                    
                    # Decode Base64
                    if isinstance(audio_data, str):
                        return base64.b64decode(audio_data)
                    return audio_data
                
                raise ValueError("No binary audio data found")

            except Exception as e:
                attempt += 1
                error_msg = str(e)
                print(f"AUDIO ERROR (Attempt {attempt}/{retries}): {error_msg}")
                
                if attempt > retries:
                    break

                # IMPLEMENTING BACKOFF WITH JITTER
                if "429" in error_msg or "500" in error_msg:
                    # Base delay grows exponentially: 2s, 4s, 8s...
                    base_delay = 2 ** attempt
                    # Jitter adds randomness (0-1s) to prevent synchronized retries
                    jitter = random.uniform(0, 1)
                    total_delay = base_delay + jitter
                    
                    print(f"⚠️ Rate Limit/Server Error. Sleeping {total_delay:.2f}s...")
                    time.sleep(total_delay)
                else:
                    # Standard short retry for other errors
                    time.sleep(2)
                    
        return None

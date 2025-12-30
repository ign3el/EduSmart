import os
import json
import base64
import time
import io
from typing import Optional, Any
from google import genai
from google.genai import types
from models import StorySchema
from pydub import AudioSegment

class GeminiService:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Using exact strings from your provided 'ListModels' output
        self.text_model = "gemini-3-flash-preview"
        self.image_model = "gemini-3-pro-image-preview"
        # 2.0-flash is supported for generateContent in your environment
        self.audio_model = "gemini-2.5-pro-preview-tts" 

    def process_file_to_story(self, file_path: str, grade_level: str) -> Optional[dict]:
        """Generates the story JSON structure with safety checks."""
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
        """Multimodal image generation with exhaustive attribute checking."""
        try:
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=f"Educational cartoon illustration: {prompt}",
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            
            # Pylance safety check: ensures no part of the chain is None
            if not (response.candidates and 
                    response.candidates[0].content and 
                    response.candidates[0].content.parts):
                return None

            for part in response.candidates[0].content.parts:
                # Fixes 'data is not a known attribute of None'
                if part.inline_data and part.inline_data.data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"IMAGE ERROR: {e}")
            return None

    def generate_voiceover(self, text: str, retries: int = 3) -> Optional[bytes]:
        """TTS logic with binary decoding and exponential backoff."""
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
                
                if not (response.candidates and 
                        response.candidates[0].content and 
                        response.candidates[0].content.parts):
                    raise ValueError("Incomplete audio response structure")

                audio_part = response.candidates[0].content.parts[0]
                
                # Verified binary access to avoid Pylance errors
                if audio_part.inline_data and audio_part.inline_data.data:
                    audio_data = audio_part.inline_data.data
                    
                    # Debug: Print data type
                    print(f"Audio data type: {type(audio_data)}")
                    
                    # Gemini returns bytes directly, not base64 string
                    if isinstance(audio_data, bytes):
                        print(f"Audio is bytes, length: {len(audio_data)}")
                        
                        # Convert to MP3 format (Gemini likely returns WAV or PCM)
                        try:
                            # Load audio data (auto-detects format)
                            audio = AudioSegment.from_file(io.BytesIO(audio_data))
                            
                            # Export as MP3
                            mp3_buffer = io.BytesIO()
                            audio.export(mp3_buffer, format="mp3", bitrate="128k")
                            mp3_bytes = mp3_buffer.getvalue()
                            
                            print(f"Converted to MP3, new length: {len(mp3_bytes)}")
                            return mp3_bytes
                        except Exception as conv_err:
                            print(f"Audio conversion error: {conv_err}")
                            # If conversion fails, return raw bytes
                            return audio_data
                    elif isinstance(audio_data, str):
                        # If it's base64 string, decode it first then convert
                        print(f"Audio is base64 string, decoding...")
                        raw_bytes = base64.b64decode(audio_data)
                        
                        try:
                            audio = AudioSegment.from_file(io.BytesIO(raw_bytes))
                            mp3_buffer = io.BytesIO()
                            audio.export(mp3_buffer, format="mp3", bitrate="128k")
                            return mp3_buffer.getvalue()
                        except Exception as conv_err:
                            print(f"Audio conversion error: {conv_err}")
                            return raw_bytes
                    else:
                        raise ValueError(f"Unexpected audio data type: {type(audio_data)}")
                
                raise ValueError("No binary audio data found in response")

            except Exception as e:
                attempt += 1
                print(f"AUDIO ERROR (Attempt {attempt}/{retries}): {e}")
                # Wait longer if hitting quota limits
                if "429" in str(e):
                    time.sleep(12 * attempt) 
                else:
                    time.sleep(2)
        return None
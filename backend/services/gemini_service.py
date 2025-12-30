import os
import json
import base64
import time
import io
import wave
from typing import Optional, Any
from google import genai
from google.genai import types
from models import StorySchema

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

            # Professional teacher-led prompt
            teacher_prompt = f"""
As a {grade_level} teacher, I need you to transform this educational content into an engaging, interactive animated storybook for my students.

TEACHING OBJECTIVES:
• Make complex concepts accessible and fun for {grade_level} learners
• Use age-appropriate language, examples, and storytelling techniques
• Create memorable characters and scenarios that students can relate to
• Ensure the content aligns with {grade_level} curriculum standards

STORY REQUIREMENTS:
1. DYNAMIC LENGTH: Analyze the content complexity and create the OPTIMAL number of scenes (typically 5-10 scenes). More complex topics need more scenes; simpler topics need fewer.

2. ENGAGING NARRATIVE:
   - Start with a captivating hook that grabs student attention
   - Introduce relatable characters (children, animals, friendly guides)
   - Use conversational, encouraging tone like a storytelling teacher
   - Include interactive elements (questions, discoveries, challenges)
   - Build excitement and curiosity throughout
   - End with a satisfying conclusion that reinforces learning

3. VISUAL DESCRIPTIONS:
   - Each scene needs vivid, colorful imagery perfect for cartoon illustrations
   - Describe settings, characters, and actions clearly for visual artists
   - Use bright, cheerful, educational cartoon style
   - Make it visually diverse to maintain engagement

4. COMPREHENSION QUIZ:
   - Create 3-5 questions based on key concepts from the story
   - Questions should test understanding, not just memorization
   - Use age-appropriate vocabulary for {grade_level}
   - Make options plausible to encourage critical thinking
   - Ensure one clearly correct answer per question
   - At the end of Quiz, display score with Review Answer tab to check all answers with explanations

TONE: Warm, encouraging, enthusiastic teacher voice that celebrates learning and discovery!

Please transform the attached document into this interactive educational story format.
"""

            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                    teacher_prompt
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
        """Generate TTS audio. Returns WAV-formatted bytes."""
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
                
                # Check MIME type if available
                if audio_part.inline_data and audio_part.inline_data.mime_type:
                    print(f"Audio MIME type: {audio_part.inline_data.mime_type}")
                
                # Verified binary access to avoid Pylance errors
                if audio_part.inline_data and audio_part.inline_data.data:
                    pcm_data = audio_part.inline_data.data
                    
                    if not isinstance(pcm_data, bytes):
                        raise ValueError(f"Expected bytes, got {type(pcm_data)}")
                    
                    print(f"PCM data size: {len(pcm_data)} bytes")
                    
                    # Gemini returns raw PCM audio - wrap it in WAV container
                    # Format: 24000 Hz, 16-bit, mono (per Gemini docs)
                    wav_buffer = io.BytesIO()
                    with wave.open(wav_buffer, 'wb') as wav_file:
                        wav_file.setnchannels(1)       # Mono
                        wav_file.setsampwidth(2)        # 16-bit (2 bytes)
                        wav_file.setframerate(24000)    # 24 kHz
                        wav_file.writeframes(pcm_data)
                    
                    wav_bytes = wav_buffer.getvalue()
                    print(f"WAV file created: {len(wav_bytes)} bytes")
                    print(f"WAV header: {wav_bytes[:16].hex()}")
                    
                    return wav_bytes
                
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
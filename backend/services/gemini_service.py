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
As a professional {grade_level} educational teacher, I need you to transform this educational content into an engaging, interactive animated storybook for my students.

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

4. COMPREHENSION QUIZ (CRITICAL - Must match {grade_level} difficulty):
   - FIRST PRIORITY: Check if the document contains an Exercise, Test, Quiz, Assessment, or Review Questions section
   - If exercise/test questions are found in the document:
     * Include ALL of those questions COMPULSORY in the quiz
     * Convert them to multiple-choice format if they aren't already
     * Preserve the original question intent and difficulty
     * Add 3-4 plausible wrong answer options if not provided
     * Keep the original correct answer
     * Generate explanations for each original question
   - TOTAL QUESTIONS REQUIRED: 
     * MINIMUM: 10 questions (can be more based on topic complexity and length)
     * MAXIMUM: No limit - scale based on content depth and complexity
     * For simple topics: 10-12 questions
     * For moderate topics: 12-15 questions
     * For complex/lengthy topics: 15-20+ questions
   - ADDITIONAL PRACTICE QUESTIONS (Always generate beyond document exercises):
     * ALWAYS add extra questions for practice, even if document already has many exercises
     * If document has fewer than 10 exercises, generate enough to reach MINIMUM 10 total
     * If document has 10+ exercises, still add 2-5 MORE practice questions
     * Analyze the style, difficulty, and format of the original exercise questions
     * Create NEW questions that MATCH the same style and complexity level
     * Mirror the question types used in the original exercises (e.g., if exercises ask about definitions, create more definition questions)
     * Use similar vocabulary and sentence structure as the original questions
     * Maintain the same difficulty level as the document's exercise questions
     * Ensure new questions test related concepts from the story
     * Example: If document has 5 exercise questions, generate 5-7 MORE = 10-12 total
     * Example: If document has 12 exercise questions, generate 3-5 MORE = 15-17 total
   - GRADE LEVEL REQUIREMENTS for any new questions:
     * KG-Grade 2: Simple yes/no, basic recall, picture-based thinking, 1-2 sentence questions
     * Grade 3-4: Short answer concepts, "what happens when", cause-effect, vocabulary in context
     * Grade 5-7: Analysis questions, "why do you think", compare/contrast, application of concepts
   - Vocabulary MUST match reading level: use words that {grade_level} students know
   - Question complexity should align with cognitive development of {grade_level}
   - Sentence length appropriate for {grade_level} (shorter for younger, more complex for older)
   - Make options plausible but distinguishable at the {grade_level} comprehension level
   - Ensure one clearly correct answer per question
   - For each question, provide an explanation that:
     * Uses vocabulary and sentence structure appropriate for {grade_level}
     * Explains why the correct answer is right in terms {grade_level} students understand
     * References specific story moments students remember
     * Encourages and celebrates learning at their level
   - Students will see these explanations in a "Review Answers" section after completing the quiz

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
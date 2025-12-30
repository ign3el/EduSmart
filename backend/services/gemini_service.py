import os
import json
import base64
import time
import io
import wave
import asyncio
import requests
import edge_tts
from urllib.parse import quote
from typing import Optional, Any
from google import genai
from google.genai import types
from models import StorySchema

class GeminiService:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Recommended models for cost efficiency and high-volume usage
        self.text_model = "gemini-2.0-flash-lite"  # Cheapest, highest quota
        self.image_model = "gemini-2.5-flash-image"  # Best balance for mass users
        self.audio_model = "gemini-2.5-flash-preview-tts"  # Optimized TTS
        # Exponential backoff configuration
        self.base_delay = 1  # Start with 1 second
        self.max_retries = 5  # Maximum retry attempts 

    def _exponential_backoff(self, attempt: int) -> int:
        """Calculate exponential backoff delay: base_delay * (2 ^ attempt)."""
        return self.base_delay * (2 ** attempt)

    def _call_with_exponential_backoff(self, func, *args, **kwargs):
        """Execute API call with exponential backoff retry logic."""
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries:
                    delay = self._exponential_backoff(attempt)
                    print(f"Attempt {attempt + 1} failed: {str(e)[:100]}... Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"All {self.max_retries + 1} attempts failed. Last error: {e}")
                    raise

    def process_file_to_story(self, file_path: str, grade_level: str) -> Optional[dict]:
        """Generates the story JSON structure with exponential backoff."""
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            # Professional teacher-led prompt (same as before)
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

            def _generate_story():
                return self.client.models.generate_content(
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
            
            response = self._call_with_exponential_backoff(_generate_story)
            
            if response and response.text:
                return json.loads(response.text)
            return None
        except Exception as e:
            print(f"STORY ERROR: {e}")
            return None

    def generate_image(self, prompt: str) -> Optional[bytes]:
        """Image generation with fallback chain: Hugging Face → Gemini (skipping Pollinations due to strict rate limits)."""
        educational_prompt = f"Educational cartoon illustration for children: {prompt}"
        
        # Try 1: Hugging Face Inference API (free with token, reliable, higher limits)
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            # Try up to 2 times with model loading wait
            for attempt in range(2):
                try:
                    print(f"Trying Hugging Face (attempt {attempt + 1}/2)...")
                    # Use SD 1.5 - faster and more likely to be loaded
                    api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
                    headers = {"Authorization": f"Bearer {hf_token}"}
                    response = requests.post(
                        api_url,
                        headers=headers,
                        json={"inputs": educational_prompt},
                        timeout=90
                    )
                    
                    if response.status_code == 200 and len(response.content) > 1000:
                        print("✓ Image generated via Hugging Face")
                        return response.content
                    elif response.status_code == 503:
                        # Model is loading, wait and retry
                        wait_time = 20 if attempt == 0 else 0
                        if wait_time > 0:
                            print(f"⚠ HF model loading, waiting {wait_time}s...")
                            time.sleep(wait_time)
                        continue
                    else:
                        print(f"HF returned status {response.status_code}")
                        break
                except Exception as e:
                    print(f"HF attempt {attempt + 1} failed: {str(e)[:80]}")
                    if attempt == 0:
                        time.sleep(2)
                    continue
        
        # Try 2: Gemini (paid fallback, always reliable)
        try:
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                print("Trying Hugging Face...")
                api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
                headers = {"Authorization": f"Bearer {hf_token}"}
                response = requests.post(
                    api_url,
                    headers=headers,
                    json={"inputs": educational_prompt},
                    timeout=60
                )
                if response.status_code == 200 and len(response.content) > 1000:
                    print("✓ Image generated via Hugging Face")
                    return response.content
        except Exception as e:
            print(f"Hugging Face failed: {str(e)[:50]}")
        
        # Try 3: Gemini (paid fallback, always reliable)
        try:
            print("Trying Gemini (paid fallback)...")
            def _generate():
                return self.client.models.generate_content(
                    model=self.image_model,
                    contents=educational_prompt,
                    config=types.GenerateContentConfig(response_modalities=["IMAGE"])
                )
            
            response = self._call_with_exponential_backoff(_generate)
            
            if not (response and response.candidates and 
                    response.candidates[0].content and 
                    response.candidates[0].content.parts):
                return None

            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    print("✓ Image generated via Gemini")
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"All image generation methods failed. Last error: {e}")
            return None

    def generate_voiceover(self, text: str) -> Optional[bytes]:
        """Generate TTS audio using Microsoft Edge-TTS (free, unlimited, ARM-compatible)."""
        async def _generate_edge_tts():
            try:
                # Use Microsoft Edge TTS with natural voice optimized for kids
                # Voice options: JennyNeural (most natural), AriaNeural (warm), GuyNeural (male)
                communicate = edge_tts.Communicate(
                    text, 
                    voice="en-US-JennyNeural",  # Most natural, expressive storytelling voice
                    rate="-10%",  # Slightly slower for clarity with kids
                    volume="+0%"
                )
                
                # Generate unique temp file to avoid conflicts
                temp_file = f"temp_audio_{os.getpid()}_{int(time.time())}.mp3"
                await communicate.save(temp_file)
                
                # Read audio as bytes
                with open(temp_file, 'rb') as f:
                    audio_bytes = f.read()
                
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
                print(f"✓ Audio generated via Edge-TTS: {len(audio_bytes)} bytes")
                return audio_bytes
                
            except Exception as e:
                print(f"Edge-TTS error: {e}")
                return None
        
        # Run async function synchronously (FastAPI compatible)
        try:
            return asyncio.run(_generate_edge_tts())
        except Exception as e:
            print(f"AUDIO GENERATION FAILED: {e}")
            return None
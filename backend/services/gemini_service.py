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
        self.text_model = "gemini-2.5-flash-lite"  # Free tier, high quota
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

⚠️ CRITICAL LANGUAGE REQUIREMENT:
• DETECT the original language of the uploaded document
• PRESERVE that exact language throughout the entire story, narration, quiz questions, and explanations
• If the document is in Arabic, generate EVERYTHING in Arabic
• If the document is in English, generate EVERYTHING in English
• If the document is in any other language, maintain that language
• DO NOT translate or change the language under any circumstances
• The story's purpose is to make the content more engaging, NOT to change its language

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
        """Image generation via RunPod (seed-capable). HF/Gemini fallbacks removed."""
        educational_prompt = f"Educational cartoon illustration for children: {prompt}"

        endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
        api_key = os.getenv("RUNPOD_KEY")

        if not endpoint_id or not api_key:
            print("RUNPOD_ENDPOINT_ID or RUNPOD_KEY not set; cannot generate image")
            return None

        # Simple spend guard (estimates). Reset monthly and block when over cap.
        cap_aed = float(os.getenv("RUNPOD_MONTHLY_CAP_AED", "25"))
        est_cost_per_image = float(os.getenv("RUNPOD_COST_AED_PER_IMAGE", "0.015"))
        usage_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runpod_usage.json")
        month_key = time.strftime("%Y-%m")

        def load_usage():
            if os.path.exists(usage_file):
                try:
                    with open(usage_file, "r") as f:
                        return json.load(f)
                except Exception:
                    return {"month": month_key, "images": 0}
            return {"month": month_key, "images": 0}

        def save_usage(data):
            try:
                with open(usage_file, "w") as f:
                    json.dump(data, f)
            except Exception as e:
                print(f"Usage file save failed: {e}")

        usage = load_usage()
        if usage.get("month") != month_key:
            usage = {"month": month_key, "images": 0}

        projected_cost = (usage.get("images", 0) + 1) * est_cost_per_image
        if cap_aed > 0 and projected_cost > cap_aed:
            print(f"RunPod cap reached (~{projected_cost:.2f} AED > {cap_aed} AED); skipping image")
            return None

        seed_env = os.getenv("RUNPOD_SEED")
        payload_input: dict[str, Any] = {"prompt": educational_prompt}
        if seed_env:
            try:
                payload_input["seed"] = int(seed_env)
            except ValueError:
                pass

        url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(url, headers=headers, json={"input": payload_input}, timeout=90)
            if resp.status_code != 200:
                print(f"RunPod returned {resp.status_code}: {resp.text[:120]}")
                return None

            data = resp.json()
            # If synchronous output is returned directly
            if data.get("status") == "COMPLETED" and data.get("output"):
                output = data.get("output")
            # Otherwise poll status endpoint
            elif data.get("id"):
                request_id = data["id"]
                status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{request_id}"
                output = None
                for _ in range(30):  # up to ~60s
                    time.sleep(2)
                    status_resp = requests.get(status_url, headers=headers, timeout=20)
                    if status_resp.status_code != 200:
                        continue
                    status_data = status_resp.json()
                    if status_data.get("status") == "COMPLETED" and status_data.get("output"):
                        output = status_data.get("output")
                        break
                    if status_data.get("status") in {"FAILED", "CANCELLED"}:
                        print(f"RunPod job failed: {status_data}")
                        return None
            else:
                print("RunPod response missing output/id")
                return None

            image_bytes = None

            def decode_b64(candidate: Any) -> Optional[bytes]:
                if isinstance(candidate, str):
                    try:
                        return base64.b64decode(candidate)
                    except Exception:
                        return None
                return None

            if isinstance(output, str):
                image_bytes = decode_b64(output)

            elif isinstance(output, dict):
                # Common patterns: {"images": [b64...]}, {"image": b64}, {"image_base64": b64}, {"output": b64 or [b64]}, nested under output
                if "images" in output and isinstance(output.get("images"), list) and output["images"]:
                    image_bytes = decode_b64(output["images"][0])
                if not image_bytes:
                    b64 = output.get("image") or output.get("image_base64")
                    image_bytes = decode_b64(b64)
                if not image_bytes:
                    inner_output = output.get("output")
                    if isinstance(inner_output, str):
                        image_bytes = decode_b64(inner_output)
                    elif isinstance(inner_output, list) and inner_output:
                        image_bytes = decode_b64(inner_output[0])
                    elif isinstance(inner_output, dict):
                        b64 = inner_output.get("image") or inner_output.get("image_base64")
                        if not b64 and isinstance(inner_output.get("images"), list) and inner_output["images"]:
                            b64 = inner_output["images"][0]
                        image_bytes = decode_b64(b64)

            elif isinstance(output, list) and output:
                first = output[0]
                if isinstance(first, str):
                    image_bytes = decode_b64(first)
                elif isinstance(first, dict):
                    b64 = first.get("image") or first.get("image_base64") or first.get("output")
                    if not b64 and isinstance(first.get("images"), list) and first["images"]:
                        b64 = first["images"][0]
                    image_bytes = decode_b64(b64)

            if image_bytes:
                usage["images"] = usage.get("images", 0) + 1
                save_usage(usage)
                print("✓ Image generated via RunPod")
                return image_bytes

            print("RunPod output could not be parsed")
            return None
        except Exception as e:
            print(f"RunPod error: {str(e)[:120]}")
            return None

    def generate_voiceover(self, text: str, voice: str = "en-US-JennyNeural") -> Optional[bytes]:
        """Generate TTS audio using Microsoft Edge-TTS (free, unlimited, ARM-compatible)."""
        async def _generate_edge_tts():
            try:
                # Use Microsoft Edge TTS with natural voice optimized for kids
                # Voice options: JennyNeural (most natural), AriaNeural (warm), GuyNeural (male)
                communicate = edge_tts.Communicate(
                    text, 
                    voice=voice,  # User-selected voice
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
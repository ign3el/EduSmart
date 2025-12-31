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
        self.text_model = "gemini-2.5-flash"  # Available model with higher rate limits than lite version
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

            # STEP 1: Extract Learning Objectives & Key Concepts
            analysis_prompt = f"""Analyze this educational document and extract:
1. Main learning objectives (what should students learn?)
2. Key concepts/topics to focus on
3. Important facts or skills to teach
4. Real-world applications or examples
5. Any specific vocabulary that must be included

Be concise and specific. The output will be used to create an accurate educational story."""

            def _analyze_document():
                return self.client.models.generate_content(
                    model=self.text_model,
                    contents=[
                        types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                        analysis_prompt
                    ]
                )
            
            analysis_response = self._call_with_exponential_backoff(_analyze_document)
            learning_objectives = analysis_response.text if analysis_response else ""

            # STEP 2: Generate Story Using Extracted Learning Objectives
            teacher_prompt = f"""You are an expert educational content creator for {grade_level} students.

DOCUMENT ANALYSIS (must use to create story):
{learning_objectives}

NOW, transform the document into an engaging educational animated storybook using ONLY the concepts, facts, and learning objectives extracted above. 

CRITICAL REQUIREMENTS:

1. STORY ACCURACY & RELEVANCE:
   - Story MUST directly teach the extracted learning objectives
   - Every scene MUST reinforce key concepts from the analysis
   - Story events must logically flow from the educational content
   - Include specific facts, numbers, or details from the document
   - Focus on the exact topic - don't go off-topic
   - Make connections between story narrative and real-world learning
   - AVOID REPETITION: Each scene should introduce NEW information or perspective
   - Vary sentence structures and narration style across scenes
   - Progress logically from introduction → exploration → understanding → application → conclusion

2. LANGUAGE: Keep the original document language throughout (Arabic stays Arabic, English stays English, etc).

3. SAFETY & AGE-APPROPRIATENESS:
   - ALL content MUST be family-friendly for {grade_level}
   - NO nudity, violence, drugs, alcohol, or inappropriate themes
   - Characters must be fully clothed
   - Educational and positive tone

4. STORY STRUCTURE:
   - Hook students with relatable characters
   - Use conversational tone with natural dialogue
   - Include interactive elements/choices
   - Build toward satisfying conclusion
   - Generate 6-10 scenes (more for complex topics)
   - Each scene advances the plot AND teaches something new
   - NO repetitive phrases or recycled descriptions

5. IMAGE DESCRIPTIONS (MOST CRITICAL - MUST MATCH NARRATION EXACTLY):
   - Each scene MUST have detailed, specific image_description (4-5 sentences minimum)
   - Image description MUST EXACTLY MATCH what happens in scene "text" field
   - If text says "Sarah picked up a red apple", image MUST show "young girl named Sarah holding a bright red apple in her hand"
   - Include ALL key visual elements mentioned in the scene text
   - Specify character names, actions, objects, colors, settings, expressions
   - REQUIREMENT: Image description should be like a detailed painting instruction
   - Examples of GOOD descriptions:
     * "Wide shot of a yellow school bus with large black letters 'SCHOOL BUS' on side, five children with backpacks waving from open windows, red octagonal stop sign extended from driver side, bright sunny day with puffy white clouds and blue sky, green trees in background"
     * "Medium shot of smiling chef named Marco wearing tall white chef hat and white apron with 'CHEF' written on it, stirring large silver pot on gas stove with wooden spoon, white steam rising, modern kitchen with wooden shelves full of glass jars containing colorful spices and ingredients"
     * "Scientific illustration showing cross-section of green plant: brown root system spreading underground in dark soil, thick green stem rising up, broad green leaves with visible veins, small water droplets glistening on leaf surface, bright yellow sun rays coming from top right corner"
   - Examples of BAD descriptions (too vague):
     * "A school scene"
     * "A cooking scene"  
     * "A plant"
   - BAD EXAMPLE: Text says "three friends exploring forest" but image says "children playing"
   - GOOD EXAMPLE: Text says "three friends exploring forest" and image says "three children aged 8-10 wearing backpacks and holding flashlights, walking between tall pine trees with brown bark, sunlight filtering through green leaves, forest floor covered with brown pine needles"

6. QUIZ (MINIMUM 10 QUESTIONS):
   - Questions MUST test understanding of the extracted learning objectives
   - Include ALL exercise/test questions from document if present
   - For simple topics: 10-12 questions
   - For moderate topics: 12-15 questions
   - For complex topics: 15-20+ questions
   - Always add extra practice questions beyond document exercises
   - Match {grade_level} difficulty and vocabulary
   - Provide clear explanations
   - One correct answer per question with 3-4 plausible options
   - For {grade_level}:
     * KG-Grade 2: Simple yes/no, basic recall, picture-based thinking
     * Grade 3-4: Concepts, cause-effect, vocabulary in context
     * Grade 5-7: Analysis, "why", compare/contrast, application
   - Question vocabulary must match {grade_level} reading level

7. TONE: Warm, encouraging, enthusiastic teacher voice that celebrates learning!

Transform the document into JSON format with this exact structure:
"""

            def _generate_story():
                return self.client.models.generate_content(
                    model=self.text_model,
                    contents=[
                        types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                        teacher_prompt,
                        "Also include document analysis context in your story design"
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

    def generate_image(self, prompt: str, scene_text: str = "", story_seed: Optional[int] = None) -> Optional[bytes]:
        """Image generation via RunPod ComfyUI FLUX.1-dev with enhanced quality prompting. Uses story_seed for character consistency."""
        # Build comprehensive, high-quality prompt for better image generation
        quality_keywords = "masterpiece, best quality, high resolution, sharp focus, detailed faces, clean linework, professional digital art, vibrant colors, clear features, well-proportioned anatomy"
        style_guide = "children's book illustration style, Disney/Pixar quality, educational cartoon, storybook art"
        safety_constraints = "[SAFETY] Family-friendly, age-appropriate, fully clothed characters, wholesome educational content"
        
        # Combine image description with scene narrative for better alignment
        # The prompt (image_description) should already be detailed, but we ensure it matches the scene
        combined_description = prompt
        
        # If scene_text is provided and prompt seems too short/vague, enhance it
        if scene_text and len(prompt.split()) < 15:
            print(f"⚠ Warning: Short image description detected. Enhancing with scene context.")
            combined_description = f"{prompt}. Story context: {scene_text[:200]}"
        
        # Build enhanced prompt with clear priority hierarchy
        enhanced_prompt = f"{quality_keywords}. {style_guide}. {safety_constraints}. MAIN VISUAL: {combined_description}"
        
        # Remove problematic terms
        enhanced_prompt = enhanced_prompt.replace("distorted", "clear")
        enhanced_prompt = enhanced_prompt.replace("blurry", "sharp")
        enhanced_prompt = enhanced_prompt.replace("ugly", "beautiful")

        # Use ComfyUI FLUX endpoint for high-quality image generation
        endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID_FLUX")
        api_key = os.getenv("RUNPOD_KEY")

        if not endpoint_id or not api_key:
            print("RUNPOD_ENDPOINT_ID_FLUX or RUNPOD_KEY not set; cannot generate image")
            return None

        # Simple spend guard (estimates). Reset monthly and block when over cap.
        cap_aed = float(os.getenv("RUNPOD_MONTHLY_CAP_AED", "25"))
        est_cost_per_image = float(os.getenv("RUNPOD_COST_AED_PER_IMAGE", "0.02"))  # FLUX is slightly more expensive
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

        # Use story-specific seed for character consistency, fall back to environment variable
        seed_value = story_seed
        if not seed_value:
            seed_env = os.getenv("RUNPOD_SEED")
            if seed_env:
                try:
                    seed_value = int(seed_env)
                except ValueError:
                    pass
        
        # Negative prompt to avoid common AI image issues
        negative_prompt = "blurry, distorted, ugly, bad anatomy, bad proportions, extra limbs, malformed hands, duplicate faces, low quality, worst quality, deformed, mutated, disfigured, poorly drawn, bad art, amateur"
        
        # ComfyUI workflow for FLUX.1-dev
        # This is a standard text-to-image workflow structure for FLUX
        workflow = {
            "6": {
                "inputs": {
                    "text": enhanced_prompt,
                    "clip": ["30", 1]  # Clip output from checkpoint loader
                },
                "class_type": "CLIPTextEncode"
            },
            "8": {
                "inputs": {
                    "samples": ["31", 0],
                    "vae": ["30", 2]
                },
                "class_type": "VAEDecode"
            },
            "9": {
                "inputs": {
                    "filename_prefix": "flux_output",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage"
            },
            "27": {
                "inputs": {
                    "width": 1024,
                    "height": 1024,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "30": {
                "inputs": {
                    "ckpt_name": "flux1-dev-fp8.safetensors"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "31": {
                "inputs": {
                    "seed": seed_value if seed_value else 42,
                    "steps": 20,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1.0,
                    "model": ["30", 0],
                    "positive": ["6", 0],
                    "negative": ["33", 0],
                    "latent_image": ["27", 0]
                },
                "class_type": "KSampler"
            },
            "33": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["30", 1]  # Clip output from checkpoint loader
                },
                "class_type": "CLIPTextEncode"
            }
        }
        
        # FLUX.1-dev payload for ComfyUI with workflow
        payload_input: dict[str, Any] = {
            "workflow": workflow
        }

        url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(url, headers=headers, json={"input": payload_input}, timeout=120)  # FLUX takes longer (~30-60s)
            if resp.status_code != 200:
                print(f"RunPod FLUX returned {resp.status_code}: {resp.text[:120]}")
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
                for _ in range(40):  # FLUX takes longer (~30-60s), poll for up to 80 seconds
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
                # Common patterns: {"images": [{"image": b64}]}, {"image": b64}, {"image_base64": b64}, {"output": b64 or [b64]}
                if "images" in output and isinstance(output.get("images"), list) and output["images"]:
                    first_image = output["images"][0]
                    if isinstance(first_image, dict):
                        # Handle {"images": [{"image": "base64..."}]}
                        b64 = first_image.get("image") or first_image.get("image_base64")
                        image_bytes = decode_b64(b64)
                    else:
                        # Handle {"images": ["base64..."]}
                        image_bytes = decode_b64(first_image)
                if not image_bytes:
                    b64 = output.get("image") or output.get("image_base64")
                    image_bytes = decode_b64(b64)
                if not image_bytes:
                    inner_output = output.get("output")
                    if isinstance(inner_output, str):
                        image_bytes = decode_b64(inner_output)
                    elif isinstance(inner_output, list) and inner_output:
                        first = inner_output[0]
                        if isinstance(first, dict):
                            b64 = first.get("image") or first.get("image_base64")
                            image_bytes = decode_b64(b64)
                        else:
                            image_bytes = decode_b64(first)
                    elif isinstance(inner_output, dict):
                        b64 = inner_output.get("image") or inner_output.get("image_base64")
                        if not b64 and isinstance(inner_output.get("images"), list) and inner_output["images"]:
                            first = inner_output["images"][0]
                            if isinstance(first, dict):
                                b64 = first.get("image") or first.get("image_base64")
                            else:
                                b64 = first
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
                print("✓ Image generated via RunPod SDXL-turbo (fast & quality)")
                return image_bytes

            print("RunPod SDXL-turbo output could not be parsed")
            return None
        except Exception as e:
            print(f"RunPod SDXL-turbo error: {str(e)[:120]}")
            return None

    def _detect_language_and_voice(self, text: str, default_voice: str) -> str:
        """Detect text language and return appropriate TTS voice."""
        # Check if text contains Arabic characters
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F')
        total_chars = sum(1 for c in text if c.isalpha())
        
        if total_chars > 0 and arabic_chars / total_chars > 0.3:
            # Arabic text detected - use Arabic voice
            return "ar-SA-HamedNeural"  # Saudi Arabic male voice, clear for kids
        
        # For other languages, use the provided voice (usually English)
        return default_voice

    def generate_voiceover(self, text: str, voice: str = "en-US-JennyNeural") -> Optional[bytes]:
        """Generate TTS audio using Microsoft Edge-TTS (free, unlimited, ARM-compatible)."""
        async def _generate_edge_tts():
            try:
                # Auto-detect language and select appropriate voice
                selected_voice = self._detect_language_and_voice(text, voice)
                
                # Use Microsoft Edge TTS with natural voice optimized for kids
                communicate = edge_tts.Communicate(
                    text, 
                    voice=selected_voice,
                    rate="-10%",  # Slightly slower for clarity with kids
                    volume="+0%"
                )
                
                # Use absolute temp file path to avoid Docker path issues
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_file = os.path.join(temp_dir, f"temp_audio_{os.getpid()}_{int(time.time() * 1000)}.mp3")
                
                # Save audio to temp file
                await communicate.save(temp_file)
                
                # Retry with exponential backoff if file not ready
                audio_bytes = None
                for attempt in range(5):
                    try:
                        await asyncio.sleep(0.05 * (attempt + 1))  # 50ms, 100ms, 150ms, 200ms, 250ms
                        if os.path.exists(temp_file):
                            with open(temp_file, 'rb') as f:
                                audio_bytes = f.read()
                            break
                    except Exception as read_error:
                        if attempt == 4:
                            raise read_error
                        continue
                
                if not audio_bytes:
                    raise FileNotFoundError(f"Failed to read temp audio file after retries: {temp_file}")
                
                # Clean up temp file safely
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as cleanup_error:
                    print(f"Temp file cleanup warning: {cleanup_error}")
                
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
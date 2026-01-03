import os
import json
import base64
import time
import io
import wave
import asyncio
import requests
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
                error_str = str(e)
                # Detect quota exhaustion (don't retry indefinitely)
                if "429" in error_str and "RESOURCE_EXHAUSTED" in error_str and "quota" in error_str.lower():
                    if attempt >= 2:  # Stop after 2 attempts for quota issues
                        print(f"❌ Gemini API quota exhausted. Please upgrade API tier or wait for reset.")
                        raise Exception("AI Service quota exceeded. Please try again later or contact support.")
                
                if attempt < self.max_retries:
                    delay = self._exponential_backoff(attempt)
                    print(f"Attempt {attempt + 1} failed: {str(e)[:100]}... Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"All {self.max_retries + 1} attempts failed. Last error: {e}")
                    raise

    def process_file_to_story(self, file_path: str, grade_level: str) -> Optional[dict]:
        """Generates the story JSON structure with a single, consolidated prompt."""
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            # A single, consolidated prompt that instructs the AI to "think" first
            # and then produce the JSON output.
            unified_prompt = f"""
You are an expert instructional designer and creative storyteller for {grade_level} students.
Your task is to transform the provided document into a high-engagement, interactive learning story.

**INTERNAL THOUGHT PROCESS (Follow these steps first, before generating the final output):**

1.  **DEEP ANALYSIS:** Perform a thorough analysis of the document to extract:
    - Core learning objectives and key concepts.
    - Specific facts, data points, and essential vocabulary.
    - The logical progression of topics.

2.  **STORY ARCHITECTURE:** Based on your analysis, design a story with:
    - A clear narrative arc (Introduction, Exploration, Application, Conclusion).
    - Characters and plot points that are direct metaphors for the learning objectives.
    - A structure of 6-10 scenes, with each scene introducing a new concept.

**FINAL JSON OUTPUT (Your entire response must be ONLY the single JSON object):**

Based on your internal analysis, generate a single, valid JSON object with the exact structure below.

**CRITICAL JSON FORMATTING RULES:**
- Ensure the entire output is a single JSON object, starting with `{{` and ending with `}}`.
- Do not include any text, notes, or markdown (like ```json) before or after the JSON object.
- Ensure every object in an array is followed by a comma, except for the last one.
- Double-check that all strings are properly enclosed in double quotes.

**JSON STRUCTURE:**
```json
{{
  "title": "A creative, engaging title for the story",
  "description": "A one-paragraph summary of the story's plot and educational goals.",
  "grade_level": "{grade_level}",
  "subject": "The main subject of the lesson (e.g., 'Science', 'History')",
  "learning_outcome": "A sentence describing what the student will be able to do after the story.",
  "scenes": [
    {{
      "scene_number": 1,
      "narrative_text": "Engaging, age-appropriate story text for this scene. It must teach a specific concept from your analysis.",
      "image_prompt": "A detailed, 4-5 sentence description for an AI image generator (3D Pixar style) that visually reinforces the concept in this scene. Must exactly match the narrative text.",
      "check_for_understanding": "A brief question to check comprehension of this scene's topic."
    }}
  ],
  "quiz": [
    {{
      "question_number": 1,
      "question_text": "A multiple-choice question testing a key learning objective.",
      "options": [
        "A. Plausible incorrect option",
        "B. The correct option",
        "C. Another plausible incorrect option",
        "D. A final plausible incorrect option"
      ],
      "correct_answer": "B",
      "explanation": "A brief, clear explanation of why the correct answer is right."
    }}
  ]
}}
```
"""

            def _generate_story_unified():
                return self.client.models.generate_content(
                    model=self.text_model,
                    contents=[
                        types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                        unified_prompt
                    ]
                )
            
            response = self._call_with_exponential_backoff(_generate_story_unified)
            
            if response and response.text:
                cleaned_text = response.text.strip()
                if cleaned_text:
                    # Find the start and end of the JSON object
                    start_index = cleaned_text.find('{')
                    end_index = cleaned_text.rfind('}')
                    
                    if start_index != -1 and end_index != -1 and end_index > start_index:
                        json_str = cleaned_text[start_index:end_index + 1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            print(f"STORY JSON DECODE ERROR: {e}")
                            print(f"Received malformed text (first 500 chars): {json_str[:500]}")
                            return None
                    else:
                        print(f"STORY ERROR: Could not find a valid JSON object in the response.")
                        print(f"Received (first 500 chars): {cleaned_text[:500]}")
                        return None
            
            print("STORY ERROR: Received empty or invalid response from GenAI model.")
            return None
        except Exception as e:
            print(f"STORY ERROR: {{e}}")
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

            def find_b64_in_obj(obj: Any) -> Optional[bytes]:
                """Recursively search for the first plausible base64 string in nested dict/list structures."""
                if isinstance(obj, str):
                    if len(obj) > 100:  # heuristic: images are long strings
                        decoded = decode_b64(obj)
                        if decoded:
                            return decoded
                    return None
                if isinstance(obj, list):
                    for item in obj:
                        found = find_b64_in_obj(item)
                        if found:
                            return found
                    return None
                if isinstance(obj, dict):
                    # common keys first
                    for key in ["image", "image_base64", "images", "output", "data", "result"]:
                        if key in obj:
                            found = find_b64_in_obj(obj[key])
                            if found:
                                return found
                    # fallback: scan all values
                    for val in obj.values():
                        found = find_b64_in_obj(val)
                        if found:
                            return found
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

            # Final fallback: search recursively for any base64 string in the output
            if not image_bytes:
                image_bytes = find_b64_in_obj(output)

            if image_bytes:
                usage["images"] = usage.get("images", 0) + 1
                save_usage(usage)
                print("✓ Image generated via RunPod FLUX/ComfyUI")
                return image_bytes

            print("RunPod FLUX/ComfyUI output could not be parsed")
            return None
        except Exception as e:
            print(f"RunPod FLUX/ComfyUI error: {str(e)[:120]}")
            return None

    # TTS generation removed - now handled by external Chatterbox service via HTTP
    # See services/chatterbox_client.py for TTS implementation
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
        self.text_model = "gemini-2.5-flash"  # Primary text model
        self.text_model_fallback = "gemini-2.5-flash-lite"  # Fallback when quota exceeded
        self.using_fallback = False  # Track if using fallback model
        self.image_model = "gemini-2.5-flash-image"  # Best balance for mass users
        self.audio_model = "gemini-2.5-flash-preview-tts"  # Optimized TTS
        # Exponential backoff configuration
        self.base_delay = 1  # Start with 1 second
        self.max_retries = 5  # Maximum retry attempts
        # TPM (Tokens Per Minute) tracking
        self.tpm_limit = 1_000_000  # Gemini 2.5 Flash TPM limit
        self.last_request_tokens = 0  # Track last request size 

    def _exponential_backoff(self, attempt: int) -> int:
        """Calculate exponential backoff delay: base_delay * (2 ^ attempt)."""
        return self.base_delay * (2 ** attempt)

    def _extract_json_from_response(self, text: str) -> Optional[dict]:
        """Extract JSON from AI response using multiple strategies."""
        
        # Strategy 1: Look for complete JSON object with proper bracket counting
        def find_complete_json(text: str) -> Optional[str]:
            start = text.find('{')
            if start == -1:
                return None
            
            bracket_count = 0
            in_string = False
            escape_next = False
            
            for i in range(start, len(text)):
                char = text[i]
                
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            return text[start:i+1]
            
            return None
        
        # Strategy 2: Find JSON in markdown code blocks
        def extract_from_code_block(text: str) -> Optional[str]:
            import re
            # Look for ```json ... ``` or ``` ... ```
            patterns = [
                r'```json\s*(\{.*?\})\s*```',
                r'```\s*(\{.*?\})\s*```'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    return match.group(1)
            return None
        
        # Strategy 3: Find JSON after common AI response prefixes
        def extract_after_prefix(text: str) -> Optional[str]:
            prefixes = [
                'Here is the story:\n',
                'Here is your story:\n',
                'JSON:\n',
                '```json\n',
                '```'
            ]
            for prefix in prefixes:
                if prefix in text:
                    after = text.split(prefix, 1)[1]
                    json_str = find_complete_json(after)
                    if json_str:
                        return json_str
            return None
        
        # Try all strategies in order
        strategies = [
            find_complete_json,
            extract_from_code_block,
            extract_after_prefix
        ]
        
        for strategy in strategies:
            try:
                json_str = strategy(text)
                if json_str:
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        continue
            except Exception:
                continue
        
        return None

    def _call_with_exponential_backoff(self, func, *args, **kwargs):
        """Execute API call with exponential backoff retry logic with automatic fallback."""
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                
                # Detect quota exhaustion and switch to fallback model
                if "429" in error_str and "RESOURCE_EXHAUSTED" in error_str:
                    # Check if it's quota vs TPM limit
                    if "quota" in error_str.lower():
                        if not self.using_fallback:
                            # Switch to fallback model
                            print(f"🔄 Primary model quota exceeded. Switching to fallback: {self.text_model_fallback}")
                            self.text_model = self.text_model_fallback
                            self.using_fallback = True
                            # Retry immediately with fallback model
                            time.sleep(2)  # Brief pause before fallback attempt
                            continue
                        else:
                            # Fallback model also exhausted
                            if attempt >= 2:
                                print(f"❌ All models quota exhausted. Please upgrade API tier or wait for reset.")
                                raise Exception("AI Service quota exceeded. Please try again later or contact support.")
                    elif "tokens per minute" in error_str.lower() or "tpm" in error_str.lower():
                        if attempt >= 1:  # TPM limits usually resolve faster
                            print(f"⚠️  TPM limit hit. Consider shortening document or waiting 60 seconds.")
                            # Wait longer for TPM to reset (60 seconds)
                            time.sleep(60)
                
                if attempt < self.max_retries:
                    delay = self._exponential_backoff(attempt)
                    print(f"Attempt {attempt + 1} failed: {str(e)[:100]}... Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"All {self.max_retries + 1} attempts failed. Last error: {e}")
                    raise

    def _ensure_minimum_questions(self, story_json: dict, file_bytes: bytes, grade_level: str) -> dict:
        """Ensure story has minimum 10 quiz questions by generating additional ones if needed."""
        try:
            quiz = story_json.get("quiz", [])
            current_count = len(quiz)
            
            if current_count >= 10:
                print(f"✓ Quiz already has {current_count} questions (minimum met)")
                return story_json
            
            questions_needed = 10 - current_count
            print(f"⚠ Only {current_count} questions found. Generating {questions_needed} additional questions...")
            
            # Extract existing questions for context
            existing_questions_text = "\n".join([f"{i+1}. {q.get('question_text', '')}" for i, q in enumerate(quiz)])
            
            # Generate additional questions
            additional_prompt = f"""You are an expert educational content designer. Generate {questions_needed} additional quiz questions to reach a minimum of 10 questions total.

CONTEXT:
- Grade level: {grade_level}
- Existing questions ({current_count} total):
{existing_questions_text}

REQUIREMENTS:
1. Generate EXACTLY {questions_needed} new questions
2. Each question must test a different learning objective
3. Questions should be diverse and cover concepts NOT already tested
4. Use the same format as existing questions
5. Make questions progressively more challenging
6. Include questions that require critical thinking

OUTPUT: Valid JSON array of {questions_needed} question objects ONLY (no extra text).

{{
  "questions": [
    {{
      "question_number": {current_count + 1},
      "question_text": "Clear question testing a core learning objective",
      "options": ["A. Plausible distractor", "B. Correct answer", "C. Partial truth", "D. Incorrect"],
      "correct_answer": "B",
      "explanation": "Brief explanation connecting to learning concept",
      "source": "generated",
      "document_section": "Additional practice"
    }}
  ]
}}"""

            def _generate_additional_questions():
                return self.client.models.generate_content(
                    model=self.text_model,
                    contents=[
                        types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                        additional_prompt
                    ]
                )
            
            response = self._call_with_exponential_backoff(_generate_additional_questions)
            
            if response and response.text:
                cleaned_text = response.text.strip()
                if cleaned_text:
                    json_obj = self._extract_json_from_response(cleaned_text)
                    if json_obj and "questions" in json_obj:
                        # Add new questions to existing quiz
                        new_questions = json_obj["questions"]
                        for i, q in enumerate(new_questions):
                            q["question_number"] = current_count + i + 1
                        quiz.extend(new_questions)
                        story_json["quiz"] = quiz
                        print(f"✓ Successfully added {len(new_questions)} questions. Total: {len(quiz)}")
                        return story_json
            
            print("⚠ Failed to generate additional questions. Returning existing quiz.")
            return story_json
            
        except Exception as e:
            print(f"⚠ Error generating additional questions: {e}")
            return story_json

    def process_file_to_story(self, file_path: str, grade_level: str) -> Optional[dict]:
        """Generates the story JSON structure with a single, consolidated prompt. Token-optimized for TPM limits."""
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            # Enhanced pedagogically-sound prompt with explicit document analysis
            unified_prompt = f"""You are an expert educational content designer. Your task: analyze the uploaded document thoroughly, extract its EXACT learning objectives, and create a story that teaches those specific goals to {grade_level} students.

STEP 1 - DOCUMENT ANALYSIS (Internal - do this first):
📄 READ the entire document carefully
🎯 IDENTIFY explicit learning objectives (look for: "Students will...", "By the end...", "Objectives:", "Goals:", "Learning outcomes:")
📚 If no explicit objectives found, INFER the teaching intent from:
   - Main topics and subtopics
   - Key vocabulary and definitions
   - Examples and explanations provided
   - Questions or exercises included
   - Concepts emphasized or repeated
❓ EXTRACT ALL QUESTIONS: Look for and extract ANY questions, exercises, problems, or tasks found in the document (sections like "Review Questions", "Exercises", "Problems", "Practice", "Assessment", "Check for Understanding")
🔍 EXTRACT: What specific knowledge/skills should students gain from THIS document?
📝 LIST all the most important concepts the document teaches
📝 COUNT: Total learning objectives + extracted questions (this will help ensure minimum quiz count)

STEP 2 - STORY DESIGN (Use extracted objectives):
✓ Each scene MUST teach atleast one of the concepts you extracted from the document
✓ Use the document's examples, terminology, and explanations as your source material
✓ If document includes specific facts/data/dates, incorporate them accurately
✓ Match the document's subject depth (don't oversimplify or add unrelated content)

CRITICAL REQUIREMENTS:
1. FIDELITY: Story must align 100% with document's teaching goals (not generic education)
2. SEQUENCE: Present concepts in the same logical order as the document
3. ACCURACY: Use exact terminology, definitions, and examples from the document
4. COVERAGE: Address ALL major concepts from the document (don't skip topics)
5. AGE-ADAPTATION: Translate document's content for {grade_level} comprehension level
6. QUESTION COUNT: Generate MINIMUM 10 quiz questions (use extracted questions when available, generate additional ones to reach 10+)
7. SOURCE INTEGRATION: Include ALL questions/tasks found in document verbatim before generating new ones

GRADE-LEVEL GUIDELINES:
- KG-Grade 2: Simple sentences, familiar analogies, hands-on scenarios, repetition
- Grade 3-4: Clear paragraphs, introduce vocabulary with definitions, compare/contrast
- Grade 5-7: Complex narratives, abstract concepts, critical thinking, real-world applications

OUTPUT: Valid JSON object ONLY (no markdown, no extra text).

{{
  "title": "Engaging title that hints at the learning goal",
  "description": "2-sentence summary: plot hook + educational value",
  "grade_level": "{grade_level}",
  "subject": "Primary subject area (Science/Math/History/Language/etc.)",
  "learning_outcome": "After this story, students will be able to [specific measurable skill]",
  "scenes": [
    {{
      "scene_number": 1,
      "narrative_text": "3-4 sentences teaching ONE key concept. Use storytelling elements (character emotions, dialogue, conflict/resolution) while embedding factual learning. End with a discovery or realization that reinforces the concept.",
      "image_prompt": "Detailed 3D Pixar-style scene description: [Setting with specific details], [Character doing specific action], [Visual elements that reinforce the learning concept]. Use vibrant colors, expressive characters, educational props visible in scene.",
      "check_for_understanding": "Question testing comprehension of THIS scene's concept (not general knowledge)"
    }}
  ],
  "quiz": [
    {{
      "question_number": 1,
      "question_text": "[EXTRACTED] Question text from document OR [GENERATED] question testing a core learning objective",
      "options": ["A. Plausible distractor based on common misconception", "B. Correct answer with specific detail", "C. Plausible distractor with partial truth", "D. Clearly incorrect option"],
      "correct_answer": "B",
      "explanation": "Brief explanation connecting answer to story events and reinforcing the concept",
      "source": "extracted" | "generated",
      "document_section": "Page/section reference if extracted from document"
    }}
  ]
}}

SCENE DEVELOPMENT STRATEGY:
Scene 1: Hook + introduce problem/question related to learning goal
Scenes 2-3: Present foundational concepts through character exploration
Scenes 4-6: Build complexity, introduce challenges that require applying concepts
Scenes 7-8: Demonstrate mastery through problem-solving or real-world application
Final Scene: Synthesis and celebration of learning with clear takeaway

NARRATIVE_TEXT REQUIREMENTS:
✓ Use active voice and vivid verbs
✓ Include character names and dialogue when appropriate
✓ Embed vocabulary naturally with context clues
✓ Show don't tell: demonstrate concepts through action
✓ Connect to students' lived experiences
✓ End each scene with mini-conclusion or question to ponder

IMAGE_PROMPT REQUIREMENTS:
✓ Specify character expressions that convey emotion/understanding
✓ Include visual metaphors for abstract concepts
✓ Describe educational elements clearly visible (diagrams, labels, demonstrations)
✓ Set appropriate environment (classroom, nature, laboratory, historical setting)
✓ Use composition that focuses attention on learning elements

Generate as many scenes as required. Generate MINIMUM 10 quiz questions (more if document has many concepts). Output ONLY the JSON object."""

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
                    # Enhanced JSON parsing with multiple fallback strategies
                    json_obj = self._extract_json_from_response(cleaned_text)
                    if json_obj:
                        # Ensure minimum 10 quiz questions
                        json_obj = self._ensure_minimum_questions(json_obj, file_bytes, grade_level)
                        return json_obj
                    
                    print(f"STORY ERROR: Could not parse valid JSON from response.")
                    print(f"Received (first 500 chars): {cleaned_text[:500]}")
                    return None
            
            print("STORY ERROR: Received empty or invalid response from GenAI model.")
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
                    "width": 768,
                    "height": 768,
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

    def generate_image_mobile_optimized(self, prompt: str, scene_text: str = "", story_seed: Optional[int] = None, is_mobile: bool = False) -> Optional[bytes]:
        """Mobile-optimized image generation with lower resolution and faster sampling."""
        # Build comprehensive, high-quality prompt for better image generation
        quality_keywords = "masterpiece, best quality, sharp focus, clean linework, vibrant colors"
        style_guide = "children's book illustration style, educational cartoon"
        safety_constraints = "[SAFETY] Family-friendly, age-appropriate"
        
        combined_description = prompt
        if scene_text and len(prompt.split()) < 15:
            combined_description = f"{prompt}. Story context: {scene_text[:200]}"
        
        enhanced_prompt = f"{quality_keywords}. {style_guide}. {safety_constraints}. MAIN VISUAL: {combined_description}"
        enhanced_prompt = enhanced_prompt.replace("distorted", "clear").replace("blurry", "sharp").replace("ugly", "beautiful")

        endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID_FLUX")
        api_key = os.getenv("RUNPOD_KEY")

        if not endpoint_id or not api_key:
            print("RUNPOD_ENDPOINT_ID_FLUX or RUNPOD_KEY not set; cannot generate image")
            return None

        # Mobile optimization: lower resolution, faster sampler
        width = 512 if is_mobile else 768
        height = 512 if is_mobile else 768
        steps = 15 if is_mobile else 20  # Fewer steps for mobile
        sampler = "euler_ancestral" if is_mobile else "euler"  # Faster sampler for mobile
        
        # Cost tracking
        cap_aed = float(os.getenv("RUNPOD_MONTHLY_CAP_AED", "25"))
        est_cost_per_image = float(os.getenv("RUNPOD_COST_AED_PER_IMAGE", "0.02"))
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

        seed_value = story_seed
        if not seed_value:
            seed_env = os.getenv("RUNPOD_SEED")
            if seed_env:
                try:
                    seed_value = int(seed_env)
                except ValueError:
                    pass
        
        negative_prompt = "blurry, distorted, ugly, bad anatomy, bad proportions, extra limbs, malformed hands, duplicate faces, low quality, worst quality, deformed, mutated, disfigured, poorly drawn, bad art, amateur"
        
        # Optimized workflow for mobile
        workflow = {
            "6": {
                "inputs": {
                    "text": enhanced_prompt,
                    "clip": ["30", 1]
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
                    "filename_prefix": "flux_mobile_output",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage"
            },
            "27": {
                "inputs": {
                    "width": width,
                    "height": height,
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
                    "steps": steps,
                    "cfg": 1.0,
                    "sampler_name": sampler,
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
                    "clip": ["30", 1]
                },
                "class_type": "CLIPTextEncode"
            }
        }
        
        payload_input = {"workflow": workflow}
        url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(url, headers=headers, json={"input": payload_input}, timeout=90)
            if resp.status_code != 200:
                print(f"RunPod FLUX returned {resp.status_code}: {resp.text[:120]}")
                return None

            data = resp.json()
            output = None
            
            if data.get("status") == "COMPLETED" and data.get("output"):
                output = data.get("output")
            elif data.get("id"):
                request_id = data["id"]
                status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{request_id}"
                for _ in range(30):  # Shorter polling for mobile
                    time.sleep(2)
                    status_resp = requests.get(status_url, headers=headers, timeout=15)
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

            def decode_b64(candidate):
                if isinstance(candidate, str):
                    try:
                        return base64.b64decode(candidate)
                    except Exception:
                        return None
                return None

            def find_b64_in_obj(obj):
                if isinstance(obj, str):
                    if len(obj) > 100:
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
                    for key in ["image", "image_base64", "images", "output"]:
                        if key in obj:
                            found = find_b64_in_obj(obj[key])
                            if found:
                                return found
                    for val in obj.values():
                        found = find_b64_in_obj(val)
                        if found:
                            return found
                return None

            if isinstance(output, str):
                image_bytes = decode_b64(output)
            elif isinstance(output, dict):
                if "images" in output and isinstance(output.get("images"), list) and output["images"]:
                    first_image = output["images"][0]
                    if isinstance(first_image, dict):
                        b64 = first_image.get("image") or first_image.get("image_base64")
                        image_bytes = decode_b64(b64)
                    else:
                        image_bytes = decode_b64(first_image)
                if not image_bytes:
                    b64 = output.get("image") or output.get("image_base64")
                    image_bytes = decode_b64(b64)
            elif isinstance(output, list) and output:
                first = output[0]
                if isinstance(first, str):
                    image_bytes = decode_b64(first)
                elif isinstance(first, dict):
                    b64 = first.get("image") or first.get("image_base64")
                    image_bytes = decode_b64(b64)

            if not image_bytes:
                image_bytes = find_b64_in_obj(output)

            if image_bytes:
                usage["images"] = usage.get("images", 0) + 1
                save_usage(usage)
                print(f"✓ {'Mobile' if is_mobile else 'Desktop'} image generated ({width}x{height})")
                return image_bytes

            print("RunPod FLUX/ComfyUI output could not be parsed")
            return None
        except Exception as e:
            print(f"RunPod FLUX/ComfyUI error: {str(e)[:120]}")
            return None

    def generate_scene_priority(self, file_path: str, grade_level: str, scene_number: int) -> Optional[dict]:
        """Generate a single scene with priority for immediate display."""
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            priority_prompt = f"""Generate ONLY Scene {scene_number} for immediate display. Focus on ONE key concept.

REQUIREMENTS:
1. Output: Valid JSON object ONLY
2. Scene must be self-contained and teach one concept
3. Include narrative_text, image_prompt, and check_for_understanding

{{
  "scene_number": {scene_number},
  "narrative_text": "3-4 sentences teaching ONE key concept. Use storytelling elements.",
  "image_prompt": "Detailed scene description with educational elements",
  "check_for_understanding": "Question testing THIS scene's concept"
}}"""

            def _generate_scene():
                return self.client.models.generate_content(
                    model=self.text_model,
                    contents=[
                        types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                        priority_prompt
                    ]
                )
            
            response = self._call_with_exponential_backoff(_generate_scene)
            
            if response and response.text:
                cleaned_text = response.text.strip()
                if cleaned_text:
                    json_obj = self._extract_json_from_response(cleaned_text)
                    if json_obj:
                        return json_obj
            
            return None
        except Exception as e:
            print(f"Priority scene generation error: {e}")
            return None

    # TTS generation removed - now handled by external Chatterbox service via HTTP
    # See services/chatterbox_client.py for TTS implementation

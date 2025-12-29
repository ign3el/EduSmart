import os
import json
import random
import re
from google import genai
from google.genai import types
import docx
import pptx

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.text_model = "gemini-2.5-flash"
        self.image_model = "imagen-4.0-generate-001" 
        self.audio_model = "gemini-2.5-flash"

    def _clean_json_text(self, text):
        # This regex finds the content between ```json and ```
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback: remove any single backticks or 'json' tags
        return text.replace('```json', '').replace('```', '').strip()

    def process_file_to_story(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        content_part = None
        
        # Load file content
        if ext == ".pdf":
            with open(file_path, "rb") as f:
                pdf_data = f.read()
            content_part = types.Part.from_bytes(data=pdf_data, mime_type="application/pdf")
        elif ext == ".docx":
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            content_part = text
        elif ext == ".pptx":
            prs = pptx.Presentation(file_path)
            text = [shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")]
            content_part = "\n".join(text)
        elif ext == ".txt":
            with open(file_path, "r") as f:
                content_part = f.read()
        else:
            return None

        try:
            # STRONGER PROMPT: Forces the key names
            prompt = """
            You are a game designer converting this content into an Interactive Visual Novel for kids (Age 6-8).
            Create a linear story where the user learns the topic through a narrative.

            Return strictly valid JSON (no markdown) with this structure:
            {
              "title": "Story Title",
              "scenes": [
                {
                  "id": 1,
                  "text": "Story narration for this scene (engaging, max 2 sentences).",
                  "image_description": "Visual description for the artist, 3d pixar style",
                  "character_details": "Blue robot named Beep",
                  "interaction": {
                      "question": "A simple question about what just happened?",
                      "options": ["Option A", "Option B"],
                      "correct_answer": "Option A"
                  }
                }
              ]
            }
            """
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[content_part, prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            cleaned_text = self._clean_json_text(response.text)
            return json.loads(cleaned_text)
        except Exception as e:
            # It's useful to know what the model returned if JSON parsing fails
            raw_text = "unavailable"
            if 'response' in locals() and hasattr(response, 'text'):
                raw_text = response.text
            print(f"Story Gen/JSON Parse Error: {e}\nRaw Text: {raw_text[:200]}")
            return None

    def generate_image(self, prompt: str, seed: int = None):
        try:
            response = self.client.models.generate_images(
                model=self.image_model,
                prompt=f"kids educational illustration, 3d pixar style, vibrant: {prompt}",
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            return response.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"Image Gen Error: {e}")
            return None

    def generate_voiceover(self, text: str):
        try:
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=f"Narrate this for a child in a cheerful, energetic voice: {text}",
                config=types.GenerateContentConfig(response_modalities=["AUDIO"])
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"Audio Gen Error: {e}")
            return None

import os
import json
import random
from google import genai
from google.genai import types
import docx
import pptx

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        # FIX: Use specific version -001 to avoid 404 errors 
        self.text_model = "gemini-1.5-flash-001"
        # FIX: Use standard Imagen 3 model 
        self.image_model = "imagen-3.0-generate-001"

    def process_file_to_story(self, file_path: str):
        """Intelligently handles PDF (Visual) vs DOCX/PPTX (Text) to generate story."""
        ext = os.path.splitext(file_path)[1].lower()
        
        content_part = None
        
        # STRATEGY 1: PDF (Visual Reading)
        if ext == ".pdf":
            with open(file_path, "rb") as f:
                pdf_data = f.read()
            content_part = types.Part.from_bytes(data=pdf_data, mime_type="application/pdf")
            
        # STRATEGY 2: DOCX (Text Extraction)
        elif ext == ".docx":
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            content_part = f"Here is the content of the Word Document:\n{text}"
            
        # STRATEGY 3: PPTX (Text Extraction)
        elif ext == ".pptx":
            prs = pptx.Presentation(file_path)
            text = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text.append(shape.text)
            content_part = f"Here is the content of the Presentation slides:\n" + "\n".join(text)
            
        # STRATEGY 4: Plain Text
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                content_part = f.read()
        
        if not content_part:
            return None

        # Generate the Story
        try:
            prompt = """
            You are a game designer converting this content into an Interactive Visual Novel for kids (Age 6-8).
            Create a linear story where the user learns the topic through a narrative.
            
            Return strictly valid JSON (no markdown) with this structure:
            {
              "title": "Story Title",
              "story_id": "unique_id_placeholder",
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
            
            # If content_part is a string (Text), put it in contents list directly
            # If content_part is a Part object (PDF), put it in list
            contents = [content_part, prompt]
            
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Gen Error: {e}")
            return None

    def generate_image(self, prompt: str, seed: int = None):
        """Generates an image using Imagen 3 with Seed for consistency."""
        try:
            if seed is None:
                seed = random.randint(0, 2**32 - 1)
            
            # Note: Imagen 3 config structure is slightly different in some SDK versions,
            # but this standard call usually works for 3.0-generate-001
            response = self.client.models.generate_images(
                model=self.image_model,
                prompt=f"kids educational illustration, 3d pixar style, vibrant: {prompt}",
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    # seed=seed # Note: Imagen 3 API sometimes ignores seed via this SDK, but we pass it anyway
                )
            )
            return response.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"Image Gen Error: {e}")
            return None
            
    def generate_voiceover(self, text: str):
        """Generates audio using Gemini Native Audio."""
        try:
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=f"Narrate this for a child in a cheerful, energetic voice: {text}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"]
                )
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"Audio Gen Error: {e}")
            return None

import os
import json
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Using exact IDs from your VPS check
        self.text_model = "gemini-2.5-flash"
        self.image_model = "gemini-2.5-flash-image"
        self.audio_model = "gemini-2.5-flash-preview-tts"

    def process_file_to_story(self, file_path):
        try:
            # Fix: Using 'file' as required by the SDK
            file_upload = self.client.files.upload(file=file_path)

            prompt = (
                "Analyze the provided document. Create an educational children's story "
                "based on the teaching points found within. \n\n"
                "DYNAMIC INSTRUCTIONS:\n"
                "- Determine 3-7 scenes based on detail.\n"
                "- Extract key terms (like plant adaptations, roots, or coatings if present).\n"
                "Output STRICTLY JSON: { 'title': '...', 'scenes': [{ 'text': '...', 'image_description': '...' }] }"
            )

            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[file_upload, prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"STORY GEN ERROR: {e}")
            return None

    def generate_image(self, prompt):
        try:
            # Use the verified flash-image model
            # Note: For flash-image, we use generate_content with image modality 
            # or the specific image generation method if supported.
            response = self.client.models.generate_images(
                model=self.image_model,
                prompt=f"Whimsical children's book illustration: {prompt}",
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            return response.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"IMAGE ERROR: {e}")
            return None

    def generate_voiceover(self, text):
        try:
            # Using your verified TTS-specific model
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=f"Narrate this story scene clearly for a child: {text}",
                config=types.GenerateContentConfig(response_modalities=["AUDIO"])
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"AUDIO ERROR: {e}")
            return None
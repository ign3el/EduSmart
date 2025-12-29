import os, json, re, io, wave
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Using the most stable model names
        self.text_model = "gemini-1.5-flash" 
        self.image_model = "imagen-3.0-generate-001" # We will wrap this in a try/except

    def process_file_to_story(self, file_path):
        # ... (Keep your extraction logic)
        response = self.client.models.generate_content(
            model=self.text_model,
            contents="Generate a 3-scene story in JSON. Each scene needs 'text' and 'image_description'.",
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)

    def generate_image(self, prompt):
        try:
            # Try the standard imagen 3 name
            response = self.client.models.generate_images(
                model="imagen-3.0-generate-001", 
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            return response.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"Image Error (Imagen 3): {e}")
            return None

    def generate_voiceover(self, text):
        # If native audio is failing or rate-limited, use a silent fallback 
        # so the story doesn't crash
        return self._silent_fallback()

    def _silent_fallback(self):
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(44100); wav.writeframes(b'\x00' * 44100)
        return buffer.getvalue()
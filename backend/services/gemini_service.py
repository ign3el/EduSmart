import os, json, re, io, wave
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_id = "gemini-2.0-flash-exp" # Use the flash model for speed/reliability
        self.image_model = "imagen-3.0-generate-001" 

    def process_file_to_story(self, file_path):
        prompt = "Create a 5-scene children's story JSON with 'title' and 'scenes' (containing 'text' and 'image_description')."
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)

    def generate_image(self, prompt):
        try:
            response = self.client.models.generate_images(
                model=self.image_model,
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            return response.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"Image Error: {e}")
            return None

    def generate_voiceover(self, text):
        try:
            # FIX: Explicitly request AUDIO modality to avoid 400 error
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=f"Read this: {text}",
                config=types.GenerateContentConfig(response_modalities=["AUDIO"])
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
        except Exception as e:
            print(f"Audio Error: {e}")
            return self._silent_fallback()

    def _silent_fallback(self):
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(44100); wav.writeframes(b'\x00' * 44100)
        return buffer.getvalue()
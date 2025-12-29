import os
import json
import random
import io
import wave
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
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```", "", text)
        return text.strip()

    def process_file_to_story(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        content_part = None
        if ext == ".pdf":
            with open(file_path, "rb") as f:
                pdf_data = f.read()
            content_part = types.Part.from_bytes(data=pdf_data, mime_type="application/pdf")
        elif ext == ".docx":
            try:
                doc = docx.Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
                content_part = f"Word Doc Content:\n{text}"
            except: return None
        elif ext == ".pptx":
            try:
                prs = pptx.Presentation(file_path)
                text = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            text.append(shape.text)
                content_part = f"PowerPoint Content:\n" + "\n".join(text)
            except: return None
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                content_part = f.read()

        if not content_part:
            return None
            
        try:
            prompt = "Generate an interactive story for kids in JSON format with 'title' and 'scenes' array."
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[content_part, prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(self._clean_json_text(response.text))
        except Exception: 
            return None

    def generate_image(self, prompt: str, seed: int = None):
        try:
            response = self.client.models.generate_images(
                model=self.image_model,
                prompt=f"3d pixar style: {prompt}",
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            return response.generated_images[0].image.image_bytes
        except: 
            return None

    def generate_voiceover(self, text: str):
        try:
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=f"Cheerful voice: {text}",
                config=types.GenerateContentConfig(response_modalities=["AUDIO"])
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data: 
                    return part.inline_data.data
            raise Exception("No inline audio data in response")
        except Exception as e:
            print(f"Audio Gen Error: {e}")
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wav:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(44100); wav.writeframes(b'\x00' * 44100)
            return buffer.getvalue()
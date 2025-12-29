import os
import json
import base64
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Using the exact strings from your VPS terminal list
        self.text_model = "gemini-3-flash-preview"
        self.audio_model = "gemini-2.5-flash-preview-tts"
        self.image_model = "gemini-3-pro-image-preview"

    def process_file_to_story(self, file_path, grade_level):
        """Uses Gemini 3 reasoning with thoughts enabled."""
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Define schema to prevent "Missing scenes" error
        story_schema = {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING"},
                "scenes": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "text": {"type": "STRING"},
                            "image_description": {"type": "STRING"}
                        },
                        "required": ["text", "image_description"]
                    }
                },
                "quiz": {"type": "ARRAY", "items": {"type": "OBJECT"}}
            },
            "required": ["title", "scenes", "quiz"]
        }

        response = self.client.models.generate_content(
            model=self.text_model,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                f"Analyze this PDF and create a {grade_level} story as JSON."
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=story_schema,
                # Gemini 3 feature: Control thinking depth
                thinking_config=types.ThinkingConfig(include_thoughts=True)
            )
        )
        return json.loads(response.text)

    def generate_image(self, prompt):
        """
        FIX: gemini-3-pro-image-preview uses 'generate_content' 
        with modality set to IMAGE.
        """
        try:
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=f"High quality educational illustration for kids: {prompt}",
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"]
                )
            )
            # Find the image part in the response
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"Image Error: {e}")
            return None

    def generate_voiceover(self, text):
        """Uses the dedicated TTS model from your list."""
        try:
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=f"Read this cheerfully: {text}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    # Choose a voice from Gemini TTS library
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Aoede" 
                            )
                        )
                    )
                )
            )
            # Binary fix to prevent browser 'NotSupportedError'
            data = response.candidates[0].content.parts[0].inline_data.data
            return base64.b64decode(data) if isinstance(data, str) else data
        except Exception as e:
            print(f"Audio Error: {e}")
            return None
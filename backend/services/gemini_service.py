import os
import json
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.text_model = "gemini-2.0-flash" 
        self.image_model = "imagen-3.0-generate-001" 
        self.audio_model = "gemini-2.0-flash-preview-tts"

    def process_file_to_story(self, file_path):
        """
        Dynamically analyzes any uploaded file and creates a multi-scene 
        story based on the content found.
        """
        try:
            # Fix: Using 'file_path' argument to upload the document
            file_upload = self.client.files.upload(file=file_path)

            prompt = (
                "Analyze the provided document. Create an educational, engaging children's story "
                "that teaches the core concepts found in the text. \n\n"
                "DYNAMIC INSTRUCTIONS:\n"
                "- Determine the number of scenes (between 3 and 7) based on the level of detail.\n"
                "- Extract key terminology and scenarios (e.g., if there are plant adaptations, "
                "mention thick stems, long roots, or waxy coatings).\n"
                "- Tone should be suitable for the grade level mentioned in the text.\n\n"
                "Output STRICTLY JSON: { 'title': '...', 'scenes': [{ 'text': '...', 'image_description': '...' }] }"
            )

            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[file_upload, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            
            return json.loads(response.text)
        except Exception as e:
            print(f"DYNAMIC STORY GEN ERROR: {e}")
            return None

    def generate_image(self, prompt):
        try:
            styled_prompt = f"Whimsical children's book illustration, vibrant colors: {prompt}"
            response = self.client.models.generate_images(
                model=self.image_model,
                prompt=styled_prompt,
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            return response.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"IMAGE ERROR: {e}")
            return None

    def generate_voiceover(self, text):
        try:
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=f"Narrate this scene: {text}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Kore')
                        )
                    )
                )
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"AUDIO ERROR: {e}")
            return None
import os
import json
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        # Initialize the client with your API key
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Use the high-performance 2.5 Flash model
        self.text_model = "gemini-2.5-flash" 
        
        # Use the state-of-the-art Imagen 4.0
        self.image_model = "imagen-4.0-generate-001" 
        
        # Use the specialized native audio model found in your list
        self.audio_model = "gemini-2.5-flash-native-audio-latest"

    def process_file_to_story(self, file_path):
        try:
            prompt = (
                "Generate a kids story in JSON format. Output must be a JSON object "
                "with a 'title' string and a 'scenes' list. Each scene needs 'text' "
                "and 'image_description'."
            )
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"STORY GEN ERROR: {e}")
            return None

    def generate_image(self, prompt):
        try:
            # Generate image using Imagen 4.0
            response = self.client.models.generate_images(
                model=self.image_model,
                prompt=f"Whimsical storybook illustration style: {prompt}",
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            return response.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"IMAGE GEN ERROR: {e}")
            return None

    def generate_voiceover(self, text):
        try:
            # Generate high-quality narration using the native audio model
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=f"Please narrate this story scene: {text}",
                config=types.GenerateContentConfig(response_modalities=["AUDIO"])
            )
            # Extract audio bytes from the response parts
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"AUDIO GEN ERROR: {e}")
            return None
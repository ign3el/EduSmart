import os
import json
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.text_model = "gemini-3-flash-preview"
        self.image_model = "gemini-3-pro-image-preview" 
        self.audio_model = "gemini-2.5-flash-preview-tts"

    def process_file_to_story(self, file_path, grade_level="Grade 4"):
        try:
            file_upload = self.client.files.upload(file=file_path)

            prompt = (
                f"You are a specialized educator for {grade_level}. Analyze the attached document and "
                f"create an age-appropriate educational story and quiz for a {grade_level} student. \n\n"
                "APPROPRIATENESS GUIDELINES:\n"
                f"- For KG-Grade 1: Use simple words, personify the plants, and keep scenes short and magical.\n"
                f"- For Grade 2-4: Use a 'discovery' narrative with relatable characters and clear cause-effect.\n"
                f"- For Grade 5-7: Use more sophisticated 'survival' or 'engineering' themes with accurate terminology.\n\n"
                "DYNAMIC STRUCTURE:\n"
                "- Create as many scenes as needed to fully explain the core concepts of the document.\n"
                "- Every scene must have a narrative text and a visual description matching the age group's style.\n"
                "- Include a quiz at the end based on the learning outcomes.\n\n"
                "Output STRICTLY JSON: { 'title': '...', 'scenes': [{ 'text': '...', 'image_description': '...' }], 'quiz': [...] }"
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
            # The prompt already contains age-appropriate visual cues from the AI's description
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=prompt, # AI now generates the full description
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="1:1")
                )
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"IMAGE ERROR: {e}")
            return None

    def generate_voiceover(self, text):
        try:
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"]
                )
            )
            
            # Verify we have a valid response with parts
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    # This is the critical check for actual audio data
                    if part.inline_data:
                        return part.inline_data.data
            return None
        except Exception as e:
            print(f"CRITICAL AUDIO GEN ERROR: {e}")
            return None
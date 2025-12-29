import os
import json
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        # Initialize the client with your API key
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Using the high-performance models available in your region
        self.text_model = "gemini-2.5-flash" 
        self.image_model = "imagen-4.0-generate-001" 
        self.audio_model = "gemini-2.5-flash-preview-tts"

    def process_file_to_story(self, file_path):
        """
        Reads the uploaded file and uses its content to generate a 
        contextually accurate story for kids.
        """
        try:
            # Step 1: Upload the file to Gemini's temporary storage to analyze it
            # This allows Gemini to 'read' the PDF directly
            file_upload = self.client.files.upload(path=file_path)

            prompt = (
                "You are an expert educator. Based on the attached document about desert plant adaptations, "
                "create a whimsical and engaging story for a Grade 4 student. "
                "The story MUST include these specific facts from the text: \n"
                "- How thick stems and fleshy leaves store water.\n"
                "- Why plants have spines or waxy coatings to prevent water loss.\n"
                "- How deep roots help plants like the Date Palm survive in the UAE desert.\n\n"
                "Output the story STRICTLY in JSON format with a 'title' string and a 'scenes' list. "
                "Each scene object must contain 'text' (the story segment) and 'image_description' "
                "(a detailed prompt for an image generator)."
            )

            # Step 2: Generate the story content
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
            print(f"STORY GEN ERROR: {e}")
            # Fallback story in case of total failure
            return {
                "title": "Desert Survival",
                "scenes": [{"text": "The desert is hot, but plants have secrets to survive!", "image_description": "A sunny desert with a cactus"}]
            }

    def generate_image(self, prompt):
        try:
            # Enhance the prompt for a consistent whimsical storybook style
            styled_prompt = f"Whimsical children's book illustration, vibrant colors, soft lighting: {prompt}"
            
            response = self.client.models.generate_images(
                model=self.image_model,
                prompt=styled_prompt,
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            return response.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"IMAGE GEN ERROR: {e}")
            return None

    def generate_voiceover(self, text):
        try:
            # Generate high-quality narration using the TTS model
            response = self.client.models.generate_content(
                model=self.audio_model,
                contents=f"Narrate this story scene for a child: {text}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name='Kore' 
                            )
                        )
                    )
                )
            )
            
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"AUDIO GEN ERROR: {e}")
            return None
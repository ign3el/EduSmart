import os
import requests
import logging

logger = logging.getLogger(__name__)

def generate_tts(text: str, voice: str = "af_sarah", speed: float = 1.0) -> bytes:
    """
    Generates TTS audio using the external Kokoro-82M service via API.
    
    Args:
        text (str): The text to convert to speech.
        voice (str): The voice ID to use (default: "af_sarah").
        speed (float): The speed of speech (default: 1.0).
        
    Returns:
        bytes: The raw audio data (WAV format).
        
    Raises:
        Exception: If the TTS service fails or returns an error.
    """
    # Secure Endpoint Configuration
    endpoint = "https://tts.ign3el.com/v1/audio/speech"
    api_key = "TTS_AHTE_2026!"
    
    payload = {
        "model": "kokoro",
        "input": text,
        "voice": voice,
        "response_format": "wav",
        "speed": speed
    }
    
    headers = {
        "TTS_API_KEY": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        # Increase timeout as TTS generation can take time
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.content
        else:
            error_msg = f"Kokoro TTS Error {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Kokoro TTS service at {endpoint}: {e}")
        raise Exception(f"TTS Service Connection Failed: {str(e)}")
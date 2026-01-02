# Type stubs for TTS package (Coqui TTS)
# This file suppresses Pylance errors when TTS isn't installed locally

from typing import Optional, Any

class TTS:
    """Coqui TTS API wrapper"""
    def __init__(
        self,
        model_name: Optional[str] = None,
        progress_bar: bool = True,
        gpu: bool = False
    ) -> None: ...
    
    def tts_to_file(
        self,
        text: str,
        file_path: Any,
        speaker: Optional[str] = None,
        language: Optional[str] = None
    ) -> None: ...

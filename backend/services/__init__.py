# Backend Services

This directory contains all the core AI services for EduStory:

## Services

### document_processor.py
- Extracts text from PDF and DOCX files
- Uses PyPDF2 and python-docx libraries
- Cleans and normalizes extracted text

### script_generator.py
- Converts educational content into interactive screenplay
- Uses LangChain + OpenAI GPT-4 for content adaptation
- Adapts language complexity based on grade level (KG-1 to Grade 7)
- Creates engaging narratives with character dialogue

### image_generator.py
- Generates consistent anime/cartoon-style scene images
- Uses Stable Diffusion or DALL-E 3
- Maintains character consistency using seed tokens
- Creates visually appealing educational illustrations

### voice_generator.py
- Generates expressive voiceovers for narration
- Uses ElevenLabs API for high-quality TTS
- Supports multiple voice profiles
- Estimates audio duration for timeline synchronization

### scene_assembler.py
- Combines screenplay, images, and audio into timeline
- Creates JSON timeline structure for frontend playback
- Manages asset synchronization
- Stores completed stories for retrieval

## Usage

All services are initialized in `main.py` and called via API endpoints.

## Configuration

Services require API keys set as environment variables:
- `OPENAI_API_KEY` for GPT-4
- `STABILITY_API_KEY` for Stable Diffusion
- `ELEVENLABS_API_KEY` for voice generation

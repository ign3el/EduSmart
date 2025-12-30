# Voice Options for Edge-TTS

## Current Voice
**en-US-JennyNeural** - Most natural, expressive storytelling voice (RECOMMENDED for kids)

---

## Top Voice Recommendations for Educational Content

### ⭐ Best for Children's Stories

| Voice | Gender | Style | Best For |
|-------|--------|-------|----------|
| **en-US-JennyNeural** | Female | Natural, expressive | 🏆 Storytelling, engaging narratives |
| **en-US-AriaNeural** | Female | Warm, clear | General education, friendly tone |
| **en-US-GuyNeural** | Male | Friendly, clear | Male perspective, variety |
| **en-US-AndrewNeural** | Male | Storytelling | Strong narrative voice |

### 🌍 British/International Options

| Voice | Gender | Accent | Best For |
|-------|--------|--------|----------|
| **en-GB-SoniaNeural** | Female | British (clear) | International audiences, pronunciation |
| **en-GB-RyanNeural** | Male | British | Male British voice |
| **en-AU-NatashaNeural** | Female | Australian | Fun, engaging |

### 📚 Professional/Learning

| Voice | Gender | Style | Best For |
|-------|--------|-------|----------|
| **en-US-SaraNeural** | Female | Professional | Formal education |
| **en-US-TonyNeural** | Male | Professional | Technical content |

---

## How to Change Voice

Edit `backend/services/gemini_service.py` line ~222:

```python
voice="en-US-JennyNeural",  # Change this line
```

### Voice Change Examples:

**For warm, friendly tone:**
```python
voice="en-US-AriaNeural",
```

**For male voice:**
```python
voice="en-US-GuyNeural",
```

**For strong storytelling:**
```python
voice="en-US-AndrewNeural",
```

**For British accent:**
```python
voice="en-GB-SoniaNeural",
```

---

## Speed Adjustment

Current: `rate="-10%"` (slightly slower for kids)

### Speed Options:

```python
rate="-20%"   # Much slower (for younger kids, difficult content)
rate="-10%"   # Slightly slower (current, good for K-2)
rate="+0%"    # Normal speed (good for grades 3-5)
rate="+10%"   # Slightly faster (good for grades 6-7)
```

---

## Advanced: Multiple Voices (Future Feature)

You could randomize voices per story or let users choose:

```python
import random

voices = [
    "en-US-JennyNeural",
    "en-US-AriaNeural", 
    "en-US-GuyNeural"
]

voice = random.choice(voices)  # Different voice each time
```

---

## Test Voices Locally

```bash
# Install edge-tts CLI
pip install edge-tts

# List all available voices
edge-tts --list-voices | grep en-US

# Test a voice
edge-tts --voice en-US-JennyNeural --text "Hello students! Welcome to our exciting adventure today." --write-media test.mp3
```

Then play `test.mp3` to hear how it sounds!

---

## Current Settings Summary

```python
voice="en-US-JennyNeural"  # Most natural storytelling voice
rate="-10%"                 # Slightly slower for clarity
volume="+0%"                # Normal volume
```

These are optimized for engaging children in educational stories.

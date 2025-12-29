# 📚 EduSmart - AI-Powered Educational Storybook Generator

Transform educational documents into engaging, animated learning experiences for students in grades KG-1 through Grade 7.

## 🌟 Features

- **📄 Document Upload**: Support for PDF and DOCX files
- **🎭 Character Selection**: Choose from 5 unique AI guide characters
- **🎨 Dynamic Scene Generation**: AI-generated anime/cartoon-style illustrations
- **🎙️ Expressive Voiceovers**: Natural text-to-speech narration
- **📊 Grade-Level Adaptation**: Content automatically adjusted for age groups
- **🎬 Interactive Playback**: Visual novel-style presentation with controls
- **💡 Learning Points**: Key concepts highlighted in each scene

## 🏗️ Architecture

### Backend (Python + FastAPI)
- **Document Processing**: PDF/DOCX text extraction
- **AI Orchestration**: LangChain workflow management
- **Script Generation**: GPT-4 for educational screenplay creation
- **Image Generation**: Stable Diffusion/DALL-E for scene visuals
- **Voice Synthesis**: ElevenLabs for expressive narration
- **Scene Assembly**: Timeline synchronization

### Frontend (React + Vite)
- **File Upload Interface**: Drag-and-drop document upload
- **Avatar Selection**: Interactive character chooser
- **Story Player**: Synchronized media playback
- **Responsive Design**: Works on desktop and mobile

### AI Services
- **OpenAI GPT-4**: Content adaptation and screenplay writing
- **Stable Diffusion/DALL-E 3**: Consistent character images
- **ElevenLabs**: High-quality voice generation

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional, for containerized deployment)

### ⚡ Two Paths Forward

#### Path A: FREE (Open-Source, Zero API Costs) ✅ **Recommended**
- No API keys needed
- Completely offline
- Self-hosted models
- **See [FREE_SETUP_GUIDE.md](FREE_SETUP_GUIDE.md) for detailed instructions**

**Cost:** $0/month | **Setup Time:** ~50 minutes

#### Path B: API-Based (Premium Quality, Paid Services)
- Higher quality outputs
- Cloud-based processing
- API rate limits apply
- **See instructions below**

**Cost:** ~$160/month | **Setup Time:** 15 minutes

### Installation

#### For FREE Setup (Recommended)
👉 **[Follow the FREE_SETUP_GUIDE.md](FREE_SETUP_GUIDE.md)**

This guide includes:
- Installing Ollama for local LLM
- Setting up local Stable Diffusion
- Configuring Piper TTS
- Redis caching setup

#### For API-Based Setup

1. **Clone the repository**
```bash
cd EduSmart
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment template and add your API keys
cp .env.example .env
# Edit .env with your API keys
```

3. **Configure for API Mode**

Edit `backend/.env`:
```env
SERVICE_MODE=api

OPENAI_API_KEY=your_openai_api_key_here
STABILITY_API_KEY=your_stability_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

4. **Frontend Setup**
```bash
cd ../frontend
npm install
```

### Running Locally

**Start Backend:**
```bash
cd backend
python main.py
# Backend runs at http://localhost:8000
```

**Start Frontend (in new terminal):**
```bash
cd frontend
npm run dev
# Frontend runs at http://localhost:3004 (VPS domain: https://edusmart.ign3el.com)
```

### Docker Deployment

```bash
# Build and run all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3004 (VPS domain: https://edusmart.ign3el.com)
# Backend API: http://localhost:8000
```

## 📖 Usage Guide

### Creating a Story

1. **Upload Document**
   - Drag and drop a PDF or DOCX file
   - Select appropriate grade level (KG-1 to Grade 7)
   - Click to proceed

2. **Choose Your Guide**
   - Select from 5 character options:
     - 🧙‍♂️ Wise Wizard
     - 🤖 Friendly Robot
     - 🐿️ Smart Squirrel
     - 👨‍🚀 Space Explorer
     - 🦕 Dino Teacher

3. **Watch the Story**
   - AI generates 5-8 educational scenes
   - Each scene includes:
     - Visual illustration
     - Character narration
     - Key learning point
   - Use playback controls to navigate

## 🔧 API Endpoints

### `POST /api/upload`
Upload educational document and initiate processing
- **Body**: Multipart form with file, grade_level, avatar_type
- **Returns**: Story ID and status

### `POST /api/generate-story/{story_id}`
Generate complete story with AI
- **Body**: StoryRequest model
- **Returns**: Timeline with scenes, images, and audio

### `GET /api/story/{story_id}`
Retrieve generated story
- **Returns**: Complete story data

### `GET /api/avatars`
Get available character options
- **Returns**: List of avatar configurations

## 🎨 Customization

### Adding New Characters

Edit `backend/services/image_generator.py`:
```python
self.character_seeds = {
    "new_character": "description with consistent visual details",
    # ...
}
```

Update `frontend/src/components/AvatarSelector.jsx`:
```javascript
const avatars = [
  {
    id: 'new_character',
    name: 'Character Name',
    description: 'Character description',
    emoji: '😊',
    color: '#hexcolor'
  },
  // ...
]
```

### Adjusting Grade Levels

Modify `backend/services/script_generator.py`:
```python
self.grade_prompts = {
    8: "Explanation for grade 8...",
    # Add more grades
}
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📦 Project Structure

```
EduSmart/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── models/
│   │   └── story.py           # Data models
│   ├── services/
│   │   ├── document_processor.py
│   │   ├── script_generator.py
│   │   ├── image_generator.py
│   │   ├── voice_generator.py
│   │   └── scene_assembler.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.jsx
│   │   │   ├── AvatarSelector.jsx
│   │   │   └── StoryPlayer.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- LangChain - AI workflow orchestration
- PyPDF2 - PDF text extraction
- python-docx - DOCX parsing

**AI Services (Choose Your Path):**

*Free & Open-Source (Recommended):*
- Ollama + Mistral/Llama 2 - Local LLM for screenplay
- Stable Diffusion + diffusers - Local image generation
- Piper TTS - Local voice synthesis
- Redis - Content caching

*Or Premium APIs:*
- OpenAI GPT-4 - Cloud-based screenplay
- Stability AI - Cloud-based image generation
- ElevenLabs - Cloud-based voice synthesis

**Frontend:**
- React 18 - UI library
- Vite - Build tool
- Framer Motion - Animations
- React Dropzone - File uploads
- Axios - HTTP client

**Deployment:**
- Docker - Containerization
- Docker Compose - Multi-container orchestration
- Nginx - Reverse proxy

## 🔐 Security Considerations

- API keys stored in environment variables
- File upload size limits enforced
- Input validation on all endpoints
- CORS configured for production
- Rate limiting recommended for production

## 📈 Scaling for Production

### Performance Optimizations
- Implement Redis caching for generated content ✅ (Built-in)
- Use CDN for static assets
- Add database for story persistence (PostgreSQL recommended)
- Implement background task queue (Celery + Redis)
- Enable response compression

### Cost Optimization
**Free Path:**
- Self-host all AI services (zero API costs)
- Cache generated assets locally
- Implement usage quotas per user
- Batch similar requests

**API Path:**
- Cache AI-generated assets
- Implement usage quotas per user
- Batch similar requests
- Use lower-cost models for initial drafts

**Estimated Costs:**
- Free Open-Source: **$0/month** (plus server hosting)
- API-Based: **~$160/month** (for 1,000 stories)

## 🐛 Troubleshooting

### Common Issues

**Import errors in backend:**
```bash
pip install -r requirements.txt
```

**Frontend won't start:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**API keys not working:**
- Check `.env` file exists in `backend/`
- Verify API keys are valid and have credits
- Ensure no spaces around `=` in `.env`

**Docker issues:**
```bash
docker-compose down
docker-compose up --build
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- OpenAI for GPT-4 and DALL-E
- Stability AI for Stable Diffusion
- ElevenLabs for voice synthesis
- LangChain for orchestration framework

## 📞 Support

For issues and questions:
- Open a GitHub issue
- Check documentation at `/docs` endpoint when backend is running

## 🗺️ Roadmap

- [ ] Multi-language support
- [ ] Interactive quizzes after stories
- [ ] Teacher dashboard for classroom use
- [ ] Student progress tracking
- [ ] Mobile app (React Native)
- [ ] Offline mode
- [ ] Custom character creation
- [ ] Story editing tools

---

**Built with ❤️ for educators and students everywhere**

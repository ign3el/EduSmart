import { useState } from 'react';
import { FaPlay, FaCheck } from 'react-icons/fa';
import './TeacherCard.css';

const TEACHERS = [
  { 
    id: "af_bella", 
    name: "Bella", 
    personality: "Warm & Expressive", 
    description: "Enthusiastic storyteller with natural emotion and varied pitch",
    lang: "en",
    sample: "Hi there! I'm Bella. Let me take you on an amazing learning adventure!",
    icon: "🌟"
  },
  { 
    id: "af_heart", 
    name: "Heart", 
    personality: "Gentle & Caring", 
    description: "Soft, nurturing voice perfect for younger learners",
    lang: "en",
    sample: "Hello sweetie! I'm Heart. Let's discover wonderful things together!",
    icon: "❤️"
  },
  { 
    id: "af_nicole", 
    name: "Nicole", 
    personality: "Energetic & Fun", 
    description: "Dynamic voice with playful enthusiasm for active learning",
    lang: "en",
    sample: "Hey! I'm Nicole! Ready to explore and have some fun learning?",
    icon: "🎧"
  },
  { 
    id: "af_sarah", 
    name: "Sarah", 
    personality: "Professional & Clear", 
    description: "Calm, articulate educator for focused instruction",
    lang: "en",
    sample: "Hello! I'm Sarah, your educational guide. I'll help make learning fun and engaging.",
    icon: "👩‍🏫"
  },
  { 
    id: "af_sky", 
    name: "Sky", 
    personality: "Bright & Cheerful", 
    description: "Light, optimistic voice that encourages curiosity",
    lang: "en",
    sample: "Hi! I'm Sky! Let's explore the world of learning together!",
    icon: "☀️"
  },
  { 
    id: "am_michael", 
    name: "Michael", 
    personality: "Wise Narrator", 
    description: "Mature male voice with authoritative storytelling",
    lang: "en",
    sample: "Greetings! I'm Michael. Let me guide you through fascinating stories.",
    icon: "📚"
  },
  { 
    id: "am_fenrir", 
    name: "Fenrir", 
    personality: "Strong & Confident", 
    description: "Powerful male voice for adventurous narratives",
    lang: "en",
    sample: "Hello! I'm Fenrir. Get ready for exciting tales of learning!",
    icon: "🐺"
  },
  { 
    id: "bf_emma", 
    name: "Emma", 
    personality: "British Elegance", 
    description: "Refined British accent with graceful storytelling",
    lang: "en",
    sample: "Good day! I'm Emma. Allow me to share marvelous stories with you.",
    icon: "🇬🇧"
  },
  { 
    id: "ar_teacher", 
    name: "Nour", 
    personality: "Arabic Educator", 
    description: "Clear Modern Standard Arabic with warm delivery",
    lang: "ar",
    sample: "مرحباً! أنا نور، معلمتك العربية. سأساعدك في رحلة تعليمية ممتعة.",
    icon: "🌙"
  }
];

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function TeacherCard({ activeVoice = "af_sarah", onVoiceSelect, detectedLanguage = "en" }) {
  const [playingVoice, setPlayingVoice] = useState(null);
  const [audioCache, setAudioCache] = useState({});

  // Filter teachers based on detected language
  const filteredTeachers = TEACHERS.filter(teacher => {
    if (detectedLanguage === 'ar') {
      return teacher.lang === 'ar';
    }
    return teacher.lang !== 'ar';
  });

  // Auto-select default voice based on language
  const defaultVoice = detectedLanguage === 'ar' ? 'ar_teacher' : 'af_bella';
  
  // If no voice is selected or current voice doesn't match language, use default
  const currentActiveVoice = filteredTeachers.find(t => t.id === activeVoice) 
    ? activeVoice 
    : defaultVoice;

  const handleCardClick = (teacherId) => {
    onVoiceSelect(teacherId);
  };

  const playSample = async (e, teacher) => {
    e.stopPropagation(); // Prevent card selection when clicking play

    if (playingVoice) return; // Prevent multiple plays

    setPlayingVoice(teacher.id);

    try {
      // Check cache first
      if (audioCache[teacher.id]) {
        const audio = new Audio(audioCache[teacher.id]);
        audio.onended = () => setPlayingVoice(null);
        audio.play();
        return;
      }

      // Use backend proxy endpoint
      const response = await fetch(`${API_URL}/api/upload/tts-preview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          text: teacher.sample,
          voice: teacher.id,
          speed: 1.0
        })
      });

      if (!response.ok) {
        throw new Error(`TTS API error: ${response.status}`);
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      // Cache the audio
      setAudioCache(prev => ({ ...prev, [teacher.id]: audioUrl }));

      const audio = new Audio(audioUrl);
      audio.onended = () => setPlayingVoice(null);
      audio.play();

    } catch (error) {
      console.error('Error playing sample:', error);
      setPlayingVoice(null);
      
      // Fallback: Show error message
      alert(`Unable to play voice sample for ${teacher.name}. Please try again.`);
    }
  };

  return (
    <div className="teacher-card-wrapper">
      <h3 className="teacher-card-title">
        {detectedLanguage === 'ar' ? '🌙 Select Arabic Teacher' : '👨‍🏫 Choose Your Teacher'}
      </h3>
      <div className="teacher-grid">
        {filteredTeachers.map(teacher => (
          <div
            key={teacher.id}
            className={`teacher-card ${currentActiveVoice === teacher.id ? 'teacher-card-active' : ''}`}
            onClick={() => handleCardClick(teacher.id)}
          >
            <div className="teacher-card-header">
              <div className="teacher-icon">{teacher.icon}</div>
              {currentActiveVoice === teacher.id && (
                <div className="teacher-selected-badge">
                  <FaCheck />
                </div>
              )}
            </div>
            
            <h4 className="teacher-name">{teacher.name}</h4>
            
            <div className="teacher-personality-badge">
              {teacher.personality}
            </div>
            
            <p className="teacher-description">{teacher.description}</p>
            
            <button
              className={`teacher-play-btn ${playingVoice === teacher.id ? 'playing' : ''}`}
              onClick={(e) => playSample(e, teacher)}
              disabled={playingVoice !== null}
            >
              <FaPlay />
              <span>{playingVoice === teacher.id ? 'Playing...' : 'Preview Voice'}</span>
            </button>
          </div>
        ))}
      </div>
      
      {filteredTeachers.length === 0 && (
        <div className="no-teachers">
          <p>No teachers available for this language.</p>
        </div>
      )}
    </div>
  );
}

export default TeacherCard;

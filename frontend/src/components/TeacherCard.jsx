import { useState } from 'react';
import { FaPlay, FaCheck } from 'react-icons/fa';
import './TeacherCard.css';

const TEACHERS = [
  { 
    id: "af_sarah", 
    name: "Sarah", 
    personality: "Educational", 
    description: "Professional US English teacher with clear pronunciation",
    lang: "en",
    sample: "Hello! I'm Sarah, your educational guide. I'll help make learning fun and engaging.",
    icon: "👩‍🏫"
  },
  { 
    id: "af_bella", 
    name: "Bella", 
    personality: "Natural", 
    description: "Warm storyteller with expressive delivery",
    lang: "en",
    sample: "Hi there! I'm Bella. Let me take you on an amazing learning adventure!",
    icon: "🌟"
  },
  { 
    id: "ar_teacher", 
    name: "Nour", 
    personality: "Educational", 
    description: "Clear Modern Standard Arabic educator",
    lang: "ar",
    sample: "مرحباً! أنا نور، معلمتك العربية. سأساعدك في رحلة تعليمية ممتعة.",
    icon: "🌙"
  }
];

const TTS_API_URL = "https://tts.ign3el.com";
const TTS_API_KEY = "TTS_AHTE_2026!";

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
  const defaultVoice = detectedLanguage === 'ar' ? 'ar_teacher' : 'af_sarah';
  
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

      // Determine endpoint based on voice
      const endpoint = teacher.id.startsWith('ar_') 
        ? `${TTS_API_URL}/tts`
        : `${TTS_API_URL}/v1/audio/speech`;

      // Build request based on endpoint
      let requestBody;
      if (teacher.id.startsWith('ar_')) {
        // Piper format for Arabic
        requestBody = {
          text: teacher.sample,
          speaker_id: teacher.id
        };
      } else {
        // Kokoro format for English
        requestBody = {
          model: "kokoro",
          input: teacher.sample,
          voice: teacher.id,
          response_format: "mp3",
          speed: 1.0
        };
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'TTS_API_KEY': TTS_API_KEY
        },
        body: JSON.stringify(requestBody)
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

import React, { useState } from 'react';
import './VoiceSelector.css';

const VOICES = [
  { id: "af_sarah", name: "Sarah", badge: "🎓 Educational", desc: "Professional US English", lang: "en" },
  { id: "ar_teacher", name: "Nour", badge: "🌍 Arabic Teacher", desc: "Clear Modern Standard Arabic", lang: "ar" },
  { id: "af_bella", name: "Bella", badge: "🔥 Top Tier", desc: "Storyteller | Most expressive", lang: "en" }
];

const VoiceSelector = ({ selectedVoice = "af_sarah", onVoiceSelect, detectedLanguage = "en" }) => {
  const [playingVoice, setPlayingVoice] = useState(null);

  // Filter voices based on detected language
  // If 'ar', show only Arabic. If 'en' (or others), show non-Arabic voices.
  const filteredVoices = VOICES.filter(voice => 
    detectedLanguage === 'ar' ? voice.lang === 'ar' : voice.lang !== 'ar'
  );

  const handleVoiceChange = async (voiceId) => {
    onVoiceSelect(voiceId);

    try {
      await fetch('/api/user/voice', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice: voiceId })
      });
    } catch (error) {
      console.error("Failed to save voice preference:", error);
    }
  };

  const handlePlayPreview = async (e, voice) => {
    e.stopPropagation(); // Prevent card selection when clicking play
    
    if (playingVoice) return; // Prevent multiple concurrent plays
    setPlayingVoice(voice.id);

    try {
      const response = await fetch('/api/admin/tts/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add Authorization header here if needed, e.g., `Bearer ${token}`
        },
        body: JSON.stringify({
          text: `Hello, I am ${voice.name}. This is a preview of my voice.`,
          voice: voice.id,
          speed: 1.0
        })
      });

      if (!response.ok) throw new Error("Preview generation failed");

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      
      audio.onended = () => {
        setPlayingVoice(null);
        URL.revokeObjectURL(url);
      };
      
      await audio.play();
    } catch (error) {
      console.error("Preview error:", error);
      setPlayingVoice(null);
      alert("Failed to play preview. Please check the console.");
    }
  };

  return (
    <div className="voice-grid-container">
      {filteredVoices.map((voice) => {
        const isActive = selectedVoice === voice.id;
        const isPlaying = playingVoice === voice.id;
        const isRTL = voice.id === 'ar_teacher';

        return (
          <div 
            key={voice.id} 
            className={`voice-card ${isActive ? 'active' : ''}`}
            onClick={() => handleVoiceChange(voice.id)}
          >
            <div className="voice-card-header">
              <h3 className="voice-name">{voice.name}</h3>
              <span className="voice-badge">{voice.badge}</span>
            </div>
            
            <p className="voice-desc" style={{ direction: isRTL ? 'rtl' : 'ltr' }}>{voice.desc}</p>
            
            <button 
              className={`play-button ${isPlaying ? 'playing' : ''}`}
              onClick={(e) => handlePlayPreview(e, voice)}
              title="Preview Voice"
            >
              {isPlaying ? (
                <span className="icon-stop">■</span>
              ) : (
                <span className="icon-play">▶</span>
              )}
            </button>

            {isActive && <div className="active-indicator">Active</div>}
          </div>
        );
      })}
    </div>
  );
};

export default VoiceSelector;
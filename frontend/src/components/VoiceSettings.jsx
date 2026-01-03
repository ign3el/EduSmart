import React from 'react';
import './VoiceSettings.css';

const VoiceSettings = ({ voice, setVoice, speed, setSpeed }) => {
    
    const voices = [
        { name: "Teacher Female", id: "af_sarah" },
        { name: "Teacher Male", id: "am_michael" },
        { name: "Storyteller", id: "af_bella" },
        { name: "British Narrator", id: "bf_emma" },
    ];

    return (
        <div className="voice-settings">
            <div className="setting-group">
                <label htmlFor="voice-select">Voice</label>
                <select 
                    id="voice-select" 
                    value={voice} 
                    onChange={(e) => setVoice(e.target.value)}
                    className="language-select"
                >
                    {voices.map(v => (
                        <option key={v.id} value={v.id}>
                            {v.name}
                        </option>
                    ))}
                </select>
            </div>

            <div className="setting-group">
                <label htmlFor="speed-slider">Pace: {speed}x</label>
                <input
                    type="range"
                    id="speed-slider"
                    min="0.5"
                    max="2.0"
                    step="0.1"
                    value={speed}
                    onChange={(e) => setSpeed(parseFloat(e.target.value))}
                    className="slider"
                />
            </div>
        </div>
    );
};

export default VoiceSettings;


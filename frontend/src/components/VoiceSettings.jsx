import React from 'react';
import './VoiceSettings.css';

const VoiceSettings = ({ language, setLanguage, speed, setSpeed, silence, setSilence }) => {
    // Piper model voices grouped by language. 
    // In a real app, this might come from an API.
    const voiceGroups = [
        {
            groupName: "English",
            voices: [
                { name: "Female - Professional (Amy)", value: "en_female_pro" },
                { name: "Male - Professional (Lessac)", value: "en_male_pro" },
                { name: "Female - British (Alba)", value: "en_female_gb" },
                { name: "Male - Narrator (Joe)", value: "en_male_clear" },
            ]
        },
        {
            groupName: "Arabic",
            voices: [
                { name: "Female - Emirati", value: "ar_female_emirati" },
                { name: "Male - Formal (Kareem)", value: "ar_male_formal" },
                { name: "Male - Quick (Kareem Low)", value: "ar_male_fast" },
            ]
        },
        {
            groupName: "Hindi",
            voices: [
                { name: "Male - Clear (Pratham)", value: "hi_male_natural" },
                { name: "Female - Warm (Priyamvada)", value: "hi_female_friendly" },
                { name: "Male - Deep (Rohan)", value: "hi_male_deep" },
            ]
        }
    ];

    return (
        <div className="voice-settings">
            <div className="setting-group">
                <label htmlFor="language-select">Language & Voice</label>
                <select 
                    id="language-select" 
                    value={language} 
                    onChange={(e) => setLanguage(e.target.value)}
                    className="language-select"
                >
                    {voiceGroups.map(group => (
                        <optgroup label={group.groupName} key={group.groupName}>
                            {group.voices.map(voice => (
                                <option key={voice.value} value={voice.value}>
                                    {voice.name}
                                </option>
                            ))}
                        </optgroup>
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

            <div className="setting-group">
                <label htmlFor="silence-slider">Gap Between Sentences: {silence}s</label>
                <input
                    type="range"
                    id="silence-slider"
                    min="0"
                    max="3"
                    step="0.1"
                    value={silence}
                    onChange={(e) => setSilence(parseFloat(e.target.value))}
                    className="slider"
                />
            </div>
        </div>
    );
};

export default VoiceSettings;

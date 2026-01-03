import { useState, useEffect } from 'react'
import { FiFile, FiEdit2 } from 'react-icons/fi'
import TeacherCard from './TeacherCard'
import './FileConfirmation.css'

function FileConfirmation({ file, gradeLevel, onConfirm, onBack, onReupload, onEditGrade }) {
  // New state for Kokoro TTS settings
  const [voice, setVoice] = useState('af_sarah');
  const [speed, setSpeed] = useState(1.0);
  const [detectedLanguage, setDetectedLanguage] = useState('en');
  const [isDetectingLanguage, setIsDetectingLanguage] = useState(false);

  const [showGradeSelector, setShowGradeSelector] = useState(false)

  // Detect language on mount
  useEffect(() => {
    detectLanguageFromFile();
  }, [file]);

  const detectLanguageFromFile = async () => {
    setIsDetectingLanguage(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload/extract-text', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        const lang = data.language_code || 'en';
        setDetectedLanguage(lang);
        
        // Auto-select appropriate voice based on language
        if (lang === 'ar') {
          setVoice('ar_teacher');
        } else {
          setVoice('af_sarah');
        }
      }
    } catch (error) {
      console.error('Language detection error:', error);
      setDetectedLanguage('en');
    } finally {
      setIsDetectingLanguage(false);
    }
  };

  const gradeLabels = {
    1: 'KG-1 / Grade 1',
    2: 'Grade 2',
    3: 'Grade 3',
    4: 'Grade 4',
    5: 'Grade 5',
    6: 'Grade 6',
    7: 'Grade 7'
  }

  const handleConfirm = () => {
    // Pass up an object with all the settings
    onConfirm({ voice, speed })
  }

  const handleGradeChange = (newGrade) => {
    onEditGrade(newGrade)
    setShowGradeSelector(false)
  }

  return (
    <div className="file-confirmation">
      <h2>✅ Confirm Your Story Settings</h2>
      <p className="subtitle">Review your selections before generating the story</p>

      <div className="confirmation-card">
        <div className="file-info">
          <FiFile className="file-icon" />
          <div>
            <h3>Uploaded File</h3>
            <p className="filename">{file.name}</p>
            <p className="filesize">({(file.size / 1024 / 1024).toFixed(2)} MB)</p>
          </div>
          <button 
            className="edit-icon-btn"
            onClick={onReupload}
            title="Re-upload file"
          >
            <FiEdit2 />
          </button>
        </div>

        <div className="grade-info">
          <div className="info-icon">📚</div>
          <div>
            <h3>Grade Level</h3>
            <p>{gradeLabels[gradeLevel]}</p>
          </div>
          <button 
            className="edit-icon-btn"
            onClick={() => setShowGradeSelector(!showGradeSelector)}
            title="Change grade level"
          >
            <FiEdit2 />
          </button>

          {showGradeSelector && (
            <div className="grade-selector-dropdown">
              {[1, 2, 3, 4, 5, 6, 7].map((grade) => (
                <button
                  key={grade}
                  className={`grade-option ${gradeLevel === grade ? 'selected' : ''}`}
                  onClick={() => handleGradeChange(grade)}
                >
                  {gradeLabels[grade]}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="voice-selection">
        {isDetectingLanguage ? (
          <div className="detecting-language">
            <p>🔍 Detecting document language...</p>
          </div>
        ) : (
          <TeacherCard 
            activeVoice={voice}
            onVoiceSelect={setVoice}
            detectedLanguage={detectedLanguage}
          />
        )}
        
        <div className="speed-control">
          <label htmlFor="speed-slider">
            <span>⚡ Narration Speed</span>
            <span className="speed-value">{speed}x</span>
          </label>
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
          <div className="speed-labels">
            <span>Slower</span>
            <span>Normal</span>
            <span>Faster</span>
          </div>
        </div>
      </div>

      <div className="confirmation-actions">
        <button className="back-btn" onClick={onBack}>
          ← Back
        </button>
        <button className="confirm-btn" onClick={handleConfirm}>
          Confirm & Generate Story →
        </button>
      </div>
    </div>
  )
}

export default FileConfirmation

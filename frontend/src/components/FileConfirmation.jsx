import { useState } from 'react'
import { FiFile, FiEdit2 } from 'react-icons/fi'
import VoiceSettings from './VoiceSettings' // Import the new component
import './FileConfirmation.css'
import './VoiceSettings.css' // Import the new CSS

function FileConfirmation({ file, gradeLevel, onConfirm, onBack, onReupload, onEditGrade }) {
  // New state for Piper TTS settings
  const [language, setLanguage] = useState('en');
  const [speed, setSpeed] = useState(1.0);
  const [silence, setSilence] = useState(0.0);

  const [showGradeSelector, setShowGradeSelector] = useState(false)

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
    onConfirm({ language, speed, silence })
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
        <h3>🎙️ Configure Narrator Voice</h3>
        <p className="voice-description">Select the language and adjust the pace of the narration.</p>
        
        <VoiceSettings 
            language={language}
            setLanguage={setLanguage}
            speed={speed}
            setSpeed={setSpeed}
            silence={silence}
            setSilence={setSilence}
        />
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

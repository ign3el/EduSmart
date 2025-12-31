import { useState } from 'react'
import { FiCheck, FiFile, FiEdit2 } from 'react-icons/fi'
import './FileConfirmation.css'

function FileConfirmation({ file, gradeLevel, onConfirm, onBack, onReupload, onEditGrade }) {
  const [selectedVoice, setSelectedVoice] = useState('en-US-JennyNeural')
  const [showGradeSelector, setShowGradeSelector] = useState(false)

  const voices = [
    { id: 'en-US-JennyNeural', name: 'Jenny (Female)', description: 'Natural, expressive storytelling' },
    { id: 'en-US-AriaNeural', name: 'Aria (Female)', description: 'Warm, clear, friendly tone' },
    { id: 'en-US-SaraNeural', name: 'Sara (Female)', description: 'Professional, engaging narrator' },
    { id: 'en-US-MichelleNeural', name: 'Michelle (Female)', description: 'Energetic, youthful storyteller' },
    { id: 'en-US-GuyNeural', name: 'Guy (Male)', description: 'Friendly, clear male voice' },
    { id: 'en-US-AndrewNeural', name: 'Andrew (Male)', description: 'Strong storytelling voice' },
    { id: 'en-US-BrianNeural', name: 'Brian (Male)', description: 'Deep, confident narrator' },
    { id: 'en-US-ChristopherNeural', name: 'Christopher (Male)', description: 'Smooth, professional voice' },
    { id: 'en-GB-SoniaNeural', name: 'Sonia (British Female)', description: 'Clear British accent' },
    { id: 'en-GB-RyanNeural', name: 'Ryan (British Male)', description: 'Distinguished British narrator' },
    { id: 'en-AU-NatashaNeural', name: 'Natasha (Australian)', description: 'Friendly Australian accent' },
    { id: 'en-IN-NeerjaNeural', name: 'Neerja (Indian Female)', description: 'Clear Indian English accent' },
  ]

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
    onConfirm(selectedVoice)
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
        <h3>🎙️ Choose Narrator Voice</h3>
        <p className="voice-description">Select the voice that will narrate your story</p>
        
        <div className="voice-grid">
          {voices.map((voice) => (
            <div
              key={voice.id}
              className={`voice-option ${selectedVoice === voice.id ? 'selected' : ''}`}
              onClick={() => setSelectedVoice(voice.id)}
            >
              <div className="voice-radio">
                {selectedVoice === voice.id && <FiCheck />}
              </div>
              <div className="voice-details">
                <h4>{voice.name}</h4>
                <p>{voice.description}</p>
              </div>
            </div>
          ))}
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

import { useState } from 'react'
import { FiCheck, FiFile, FiEdit2 } from 'react-icons/fi'
import './FileConfirmation.css'

function FileConfirmation({ file, gradeLevel, onConfirm, onBack, onReupload, onEditGrade }) {
  const [selectedVoice, setSelectedVoice] = useState('The Wise Elder')
  const [showGradeSelector, setShowGradeSelector] = useState(false)

  const voices = [
    { id: 'The Wise Elder', name: 'The Wise Elder (M)', description: '⭐⭐⭐⭐⭐ Deep, slow, and gravelly; perfect for wizards or kings.' },
    { id: 'The Curious Child', name: 'The Curious Child (F)', description: '⭐⭐⭐⭐⭐ High pitch, energetic, and slightly breathless.' },
    { id: 'The Fairy Godmother', name: 'The Fairy Godmother (F)', description: '⭐⭐⭐⭐⭐ Very soft, breathy, and soothing; ideal for bedtime.' },
    { id: 'The Storyteller', name: 'The Storyteller (M)', description: '⭐⭐⭐⭐ Very rhythmic with a pleasant lilt; keeps attention well.' },
    { id: 'The Bold Knight', name: 'The Bold Knight (M)', description: '⭐⭐⭐⭐ Authoritative and strong; good for action sequences.' },
    { id: 'The Helpful Guide', name: 'The Helpful Guide (F)', description: '⭐⭐⭐⭐ Bright, friendly, and very high energy.' },
    { id: 'The Magical Spirit', name: 'The Magical Spirit (F)', description: '⭐⭐⭐⭐ Airy and resonant; sounds slightly ethereal.' },
    { id: 'The Fast Rabbit', name: 'The Fast Rabbit (F)', description: '⭐⭐⭐⭐ Rapid cadence; great for energetic or nervous characters.' },
    { id: 'The Giant', name: 'The Giant (M)', description: '⭐⭐⭐⭐ Very deep and slow; one of the lowest male voices.' },
    { id: 'The Classic Narrator', name: 'The Classic Narrator (F)', description: '⭐⭐⭐ Standard Southern English; very clear and articulate.' },
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

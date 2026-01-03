import { useState } from 'react'
import { FiCheck, FiFile, FiEdit2 } from 'react-icons/fi'
import './FileConfirmation.css'

function FileConfirmation({ file, gradeLevel, onConfirm, onBack, onReupload, onEditGrade }) {
  const [selectedVoice, setSelectedVoice] = useState('Ana Florence')
  const [showGradeSelector, setShowGradeSelector] = useState(false)

  const voices = [
    { id: 'Ana Florence', name: 'Ana Florence', description: 'High-energy, bright, and youthful. The Hero/Lead Character.' },
    { id: 'Abrahan Mack', name: 'Abrahan Mack', description: 'Deep, gravelly, and very warm. The Wise Narrator.' },
    { id: 'Claribel Dervla', name: 'Claribel Dervla', description: 'Soft, melodic, and soothing. The Fairy/Mother.' },
    { id: 'Lidiya Szekeres', name: 'Lidiya Szekeres', description: 'Very animated and rhythmic. The Villain/Funny Character.' },
    { id: 'Damien Black', name: 'Damien Black', description: 'Smooth, mysterious, and cool. The Mystery/Antagonist.' },
    { id: 'Daisy Studious', name: 'Daisy Studious', description: 'Clear, intelligent, and cheerful. The Teacher/Explainer.' },
    { id: 'Viktor Eka', name: 'Viktor Eka', description: 'Rugged and stout. The Giant/Troll.' },
    { id: 'Nova Hogarth', name: 'Nova Hogarth', description: 'Whimsical and airy. The Dreamer.' },
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

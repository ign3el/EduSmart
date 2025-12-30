import { useState } from 'react'
import { motion } from 'framer-motion'
import './SaveStoryModal.css'

function SaveStoryModal({ jobId, onSave, onCancel }) {
  const [storyName, setStoryName] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!storyName.trim()) return
    
    setSaving(true)
    try {
      const formData = new FormData()
      formData.append('story_name', storyName.trim())
      
      const response = await fetch(`/api/save-story/${jobId}`, {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) throw new Error('Failed to save story')
      
      const result = await response.json()
      onSave(result.story_id, storyName)
    } catch (error) {
      alert('Failed to save story: ' + error.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <motion.div 
      className="modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onCancel}
    >
      <motion.div 
        className="modal-content"
        initial={{ scale: 0.8, y: 50 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.8, y: 50 }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2>💾 Save Your Story</h2>
        <input
          type="text"
          placeholder="Enter story name..."
          value={storyName}
          onChange={(e) => setStoryName(e.target.value)}
          maxLength={50}
          autoFocus
          onKeyPress={(e) => e.key === 'Enter' && handleSave()}
        />
        <div className="modal-buttons">
          <button className="cancel-btn" onClick={onCancel} disabled={saving}>
            Cancel
          </button>
          <button 
            className="save-btn" 
            onClick={handleSave}
            disabled={!storyName.trim() || saving}
          >
            {saving ? 'Saving...' : 'Save Story'}
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

export default SaveStoryModal

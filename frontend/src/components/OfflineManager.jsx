import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import './OfflineManager.css'

function OfflineManager({ onLoadOffline, onBack }) {
  const [onlineStories, setOnlineStories] = useState([])
  const [localStories, setLocalStories] = useState([])
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [loading, setLoading] = useState(false)

  const loadLocalStories = () => {
    const stories = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key?.startsWith('edusmart_story_')) {
        try {
          const story = JSON.parse(localStorage.getItem(key))
          stories.push(story)
        } catch (error) {
          console.error('Error loading story:', error)
        }
      }
    }
    stories.sort((a, b) => b.savedAt - a.savedAt)
    setLocalStories(stories)
  }

  useEffect(() => {
    loadLocalStories()
    if (isOnline) {
      loadOnlineStories()
    }
    
    const handleOnline = () => {
      setIsOnline(true)
      loadOnlineStories()
    }
    const handleOffline = () => setIsOnline(false)
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const loadOnlineStories = async () => {
    try {
      const response = await fetch('/api/list-stories')
      if (!response.ok) throw new Error('Failed to fetch online stories')
      const data = await response.json()
      setOnlineStories(data)
    } catch (error) {
      console.error('Error loading online stories:', error)
    }
  }

  const saveToLocal = async (storyData, storyName) => {
    try {
      const storyId = `local_${Date.now()}`
      const localStory = {
        id: storyId,
        name: storyName,
        storyData: storyData,
        savedAt: Date.now(),
        isOffline: true
      }
      
      localStorage.setItem(`edusmart_story_${storyId}`, JSON.stringify(localStory))
      setLocalStories(prev => [localStory, ...prev])
      
      return storyId
    } catch (error) {
      throw new Error('Failed to save locally: ' + error.message)
    }
  }

  const loadFromLocal = (storyId) => {
    try {
      const storyData = JSON.parse(localStorage.getItem(`edusmart_story_${storyId}`))
      onLoadOffline(storyData.storyData, storyData.name)
    } catch (error) {
      alert('Failed to load story: ' + error.message)
    }
  }

  const deleteLocal = (storyId) => {
    if (confirm('Delete this local story?')) {
      localStorage.removeItem(`edusmart_story_${storyId}`)
      setLocalStories(prev => prev.filter(s => s.id !== storyId))
    }
  }

  const exportStory = async (storyId) => {
    if (!isOnline) {
      alert('Export requires internet connection')
      return
    }
    
    try {
      setLoading(true)
      const response = await fetch(`/api/export-story/${storyId}`)
      if (!response.ok) throw new Error('Export failed')
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `story_${storyId}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      alert('Export failed: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const importStory = async (event) => {
    const file = event.target.files[0]
    if (!file) return
    
    if (!isOnline) {
      alert('Import requires internet connection')
      return
    }
    
    try {
      setLoading(true)
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('/api/import-story', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) throw new Error('Import failed')
      
      const result = await response.json()
      alert(`Story "${result.name}" imported successfully!`)
      
      // Refresh the online stories list (you might want to call a parent function here)
      window.location.reload()
    } catch (error) {
      alert('Import failed: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleDateString() + ' ' + 
           new Date(timestamp).toLocaleTimeString()
  }

  return (
    <motion.div 
      className="offline-manager"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="offline-header">
        <h2>📱 Offline Story Manager</h2>
        <div className={`connection-status ${isOnline ? 'online' : 'offline'}`}>
          {isOnline ? '🟢 Online' : '🔴 Offline'}
        </div>
      </div>

      <div className="offline-actions">
      <div className="action-section">
          <h3>📤 Export Online Stories</h3>
          <p>Download stories for offline use</p>
          {onlineStories.length > 0 ? (
            <div className="export-list">
              {onlineStories.slice(0, 3).map((story) => (
                <div key={story.id} className="export-item">
                  <span>{story.name}</span>
                  <button 
                    className="export-btn"
                    onClick={() => exportStory(story.id)}
                    disabled={loading}
                  >
                    📥 Export
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-export">No online stories to export</p>
          )}
        </div>

        <div className="action-section">
          <h3>� Import Stories</h3>
          <p>Upload exported story packages</p>
          <input
            type="file"
            accept=".zip"
            onChange={importStory}
            style={{ display: 'none' }}
            id="import-file"
          />
          <label htmlFor="import-file" className="action-btn import-btn">
            📁 Import Story
          </label>
        </div>
      </div>

      <div className="offline-footer">
        <button className="back-btn" onClick={onBack}>
          ← Back to Home
        </button>
      </div>

      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Processing...</p>
        </div>
      )}
    </motion.div>
  )
}

export default OfflineManager

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import './OfflineManager.css'

function OfflineManager({ onLoadOffline, onBack }) {
  const [onlineStories, setOnlineStories] = useState([])
  const [localStories, setLocalStories] = useState([])
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [downloading, setDownloading] = useState(null)
  const [downloadMessage, setDownloadMessage] = useState('')

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
    const handleStorage = (event) => {
      if (event.key?.startsWith('edusmart_story_')) {
        loadLocalStories()
      }
    }
    
    const handleOnline = () => {
      setIsOnline(true)
      loadOnlineStories()
    }
    const handleOffline = () => setIsOnline(false)
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    window.addEventListener('storage', handleStorage)
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('storage', handleStorage)
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

  const exportStory = async (storyId, storyName) => {
    if (!isOnline) {
      alert('Export requires internet connection')
      return
    }
    
    setDownloading(storyId)
    setDownloadMessage('Zipping file...')
    
    try {
      // Step 1: Request ZIP creation
      const response = await fetch(`/api/export-story/${storyId}`)
      if (!response.ok) throw new Error('Export failed')
      
      // Step 2: Download
      setDownloadMessage('Downloading...')
      const blob = await response.blob()
      
      // Step 3: Save
      setDownloadMessage('Saving file...')
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${storyName.replace(/\s+/g, '_')}_${storyId.substring(0, 8)}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      // Step 4: Complete
      setDownloadMessage('Complete! ✓')
      
      // Clear message after delay
      setTimeout(() => {
        setDownloadMessage('')
        setDownloading(null)
      }, 2000)
    } catch (error) {
      setDownloadMessage(`Error: ${error.message}`)
      setTimeout(() => {
        setDownloadMessage('')
        setDownloading(null)
      }, 3000)
    }
  }

  const importStory = async (event) => {
    const file = event.target.files[0]
    if (!file) return
    
    // Reset file input
    event.target.value = null
    
    if (!isOnline) {
      alert('Import requires internet connection')
      return
    }
    
    setDownloading('import')
    setDownloadMessage('Uploading story...')
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('/api/import-story', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) throw new Error('Import failed')
      
      setDownloadMessage('Downloading...')
      const result = await response.json()
      
      // Load the story data from the backend
      setDownloadMessage('Saving file...')
      const storyResponse = await fetch(`/api/load-story/${result.story_id}`)
      if (!storyResponse.ok) throw new Error('Failed to load imported story')
      
      const storyData = await storyResponse.json()
      
      // Save to localStorage
      const localStoryId = `local_${Date.now()}`
      const localStory = {
        id: localStoryId,
        name: result.name,
        storyData: storyData.story_data,
        savedAt: Date.now(),
        isOffline: true
      }
      
      localStorage.setItem(`edusmart_story_${localStoryId}`, JSON.stringify(localStory))
      
      setDownloadMessage('Complete! ✓')
      
      // Navigate to story player after brief delay
      setTimeout(() => {
        setDownloadMessage('')
        setDownloading(null)
        onLoadOffline(storyData.story_data, result.name)
      }, 1000)
    } catch (error) {
      setDownloadMessage(`Error: ${error.message}`)
      setTimeout(() => {
        setDownloadMessage('')
        setDownloading(null)
      }, 3000)
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
                    onClick={() => exportStory(story.id, story.name)}
                    disabled={downloading !== null}
                  >
                    {downloading === story.id ? '⏳ Downloading...' : '📥 Export'}
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-export">No online stories to export</p>
          )}
        </div>

        <div className="action-section">
          <h3>📥 Import Stories</h3>
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

      <div className="offline-library">
        <div className="library-header">
          <div>
            <h3>🎒 Offline Stories</h3>
            <p>Play adventures you've saved for offline fun.</p>
          </div>
          <button className="refresh-btn" onClick={loadLocalStories}>↻ Refresh</button>
        </div>

        {localStories.length === 0 ? (
          <div className="empty-state">
            <div className="empty-emoji">🌟</div>
            <div>
              <h4>No offline stories yet</h4>
              <p>Export a story or save one locally to see it here.</p>
            </div>
          </div>
        ) : (
          <div className="story-grid">
            {localStories.map((story, index) => (
              <div key={story.id} className={`story-card variant-${(index % 4) + 1}`}>
                <div className="story-card-top">
                  <span className="story-chip">Offline ready</span>
                  <span className="story-date">Saved {formatDate(story.savedAt)}</span>
                </div>
                <h4>{story.name || 'Untitled Story'}</h4>
                <p className="story-subtext">{story.storyData?.title || 'Ready to play anywhere.'}</p>
                <div className="story-card-actions">
                  <button className="story-btn primary" onClick={() => loadFromLocal(story.id)}>▶ Play</button>
                  <button className="story-btn ghost" onClick={() => deleteLocal(story.id)}>🗑 Delete</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="offline-footer">
        <button className="back-btn" onClick={onBack}>
          ← Back to Home
        </button>
      </div>

      <AnimatePresence>
        {downloadMessage && (
          <motion.div 
            className="download-popup"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
          >
            <div className="download-popup-content">
              <div>
                <div className="spinner"></div>
              </div>
              <p>{downloadMessage}</p>
              
              {/* Progress Bar */}
              <div className="progress-bar-container">
                <div 
                  className="progress-bar"
                  style={{
                    width: downloadMessage.includes('Uploading') || downloadMessage.includes('Zipping') ? '25%' : 
                           downloadMessage === 'Downloading...' ? '60%' : 
                           downloadMessage === 'Saving file...' ? '85%' : '100%',
                    transition: 'width 0.4s ease'
                  }}
                ></div>
              </div>
              
              {/* Step Indicators */}
              <div className="progress-steps">
                <div className={`progress-step ${(downloadMessage.includes('Uploading') || downloadMessage.includes('Zipping')) ? 'active' : (downloadMessage === 'Downloading...' || downloadMessage === 'Saving file...' || downloadMessage === 'Complete! ✓') ? 'completed' : ''}`}>
                  <div className="step-dot">1</div>
                  <span>{downloadMessage.includes('Uploading') ? 'Upload' : 'Zip'}</span>
                </div>
                <div className={`progress-step ${downloadMessage === 'Downloading...' ? 'active' : (downloadMessage === 'Saving file...' || downloadMessage === 'Complete! ✓') ? 'completed' : ''}`}>
                  <div className="step-dot">2</div>
                  <span>Download</span>
                </div>
                <div className={`progress-step ${downloadMessage === 'Saving file...' ? 'active' : downloadMessage === 'Complete! ✓' ? 'completed' : ''}`}>
                  <div className="step-dot">3</div>
                  <span>Save</span>
                </div>
                <div className={`progress-step ${downloadMessage === 'Complete! ✓' ? 'completed' : ''}`}>
                  <div className="step-dot">✓</div>
                  <span>Done</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default OfflineManager

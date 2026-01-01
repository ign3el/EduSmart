import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import './LoadStory.css'

function LoadStory({ onLoad, onBack }) {
  const [stories, setStories] = useState([])
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(null)
  const [downloadMessage, setDownloadMessage] = useState('')

  useEffect(() => {
    fetchStories()
  }, [])

  const fetchStories = async () => {
    try {
      const response = await fetch('/api/list-stories')
      if (!response.ok) throw new Error('Failed to fetch stories')
      const data = await response.json()
      setStories(data)
    } catch (error) {
      console.error('Error fetching stories:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLoad = async (storyId) => {
    try {
      const response = await fetch(`/api/load-story/${storyId}`)
      if (!response.ok) throw new Error('Failed to load story')
      const data = await response.json()
      onLoad(data.story_data, data.name, storyId)
    } catch (error) {
      alert('Failed to load story: ' + error.message)
    }
  }

  const handleDelete = async (storyId, storyName) => {
    if (!confirm(`Delete "${storyName}"? This cannot be undone.`)) return
    
    try {
      const response = await fetch(`/api/delete-story/${storyId}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Failed to delete story')
      
      setStories(stories.filter(s => s.id !== storyId))
    } catch (error) {
      alert('Failed to delete story: ' + error.message)
    }
  }

  const handleDownload = async (storyId, storyName) => {
    setDownloading(storyId)
    setDownloadMessage('Zipping file...')
    
    try {
      // Step 1: Request ZIP creation
      const response = await fetch(`/api/export-story/${storyId}`)
      
      if (!response.ok) throw new Error('Failed to download story')
      
      // Step 2: Download
      setDownloadMessage('Downloading...')
      const blob = await response.blob()
      
      // Step 3: Save
      setDownloadMessage('Saving file...')
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${storyName.replace(/\s+/g, '_')}_${storyId.substring(0, 8)}.zip`
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
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

  const formatDate = (timestamp) => {
    const date = new Date(parseInt(timestamp) / 10000 - 12219292800000)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
  }

  return (
    <motion.div 
      className="load-story-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <h2>📚 Your Saved Stories</h2>
      
      {loading ? (
        <div className="loading-stories">Loading stories...</div>
      ) : stories.length === 0 ? (
        <div className="no-stories">
          <p>🎭 No saved stories yet!</p>
          <p>Create and save your first story to see it here.</p>
        </div>
      ) : (
        <div className="stories-grid">
          {stories.map((story) => (
            <motion.div
              key={story.id}
              className="story-card"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <h3>{story.name}</h3>
              <div className="story-date">
                📅 {formatDate(story.saved_at)}
              </div>
              <div className="story-card-actions">
                <button 
                  className="load-btn"
                  onClick={() => handleLoad(story.id)}
                >
                  Load Story
                </button>
                <button 
                  className="download-btn"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDownload(story.id, story.name)
                  }}
                  disabled={downloading !== null}
                  title="Download as ZIP file"
                >
                  {downloading === story.id ? '⏳ Downloading...' : '⬇️ Download'}
                </button>
                <button 
                  className="delete-btn"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(story.id, story.name)
                  }}
                >
                  Delete
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
      
      <button className="back-button" onClick={onBack}>
        ← Back to Home
      </button>

      {/* Download Status Popup */}
      {downloadMessage && (
        <div className="download-popup">
          <motion.div 
            className="download-popup-content"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {downloadMessage !== 'Complete! ✓' ? <div className="spinner"></div> : <span style={{ fontSize: '1.2rem' }}>✓</span>}
              <p style={{ margin: 0 }}>{downloadMessage}</p>
            </div>
            
            {/* Progress Bar */}
            <div className="progress-bar-container">
              <div 
                className="progress-bar"
                style={{
                  width: downloadMessage === 'Zipping file...' ? '25%' : 
                         downloadMessage === 'Downloading...' ? '60%' : 
                         downloadMessage === 'Saving file...' ? '85%' : '100%',
                  transition: 'width 0.4s ease'
                }}
              ></div>
            </div>
            
            {/* Step Indicators */}
            <div className="progress-steps">
              <div className={`progress-step ${downloadMessage === 'Zipping file...' ? 'active' : downloadMessage === 'Downloading...' || downloadMessage === 'Saving file...' || downloadMessage === 'Complete! ✓' ? 'completed' : ''}`}>
                <div className="step-dot">1</div>
                <span>Zip</span>
              </div>
              <div className={`progress-step ${downloadMessage === 'Downloading...' ? 'active' : downloadMessage === 'Saving file...' || downloadMessage === 'Complete! ✓' ? 'completed' : ''}`}>
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
          </motion.div>
        </div>
      )}
    </motion.div>
  )
}

export default LoadStory

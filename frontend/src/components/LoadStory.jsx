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
      onLoad(data.story_data, data.name)
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
    setDownloadMessage('Preparing download...')
    
    try {
      setDownloadMessage('Fetching story files...')
      const response = await fetch(`/api/export-story/${storyId}`)
      
      if (!response.ok) throw new Error('Failed to download story')
      
      setDownloadMessage('Creating ZIP file...')
      const blob = await response.blob()
      
      setDownloadMessage('Starting download...')
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${storyName.replace(/\s+/g, '_')}_${storyId.substring(0, 8)}.zip`
      
      // Use setTimeout to allow UI to update
      setTimeout(() => {
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        setDownloadMessage('')
        setDownloading(null)
      }, 100)
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
        <motion.div 
          className="download-popup"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
        >
          <div className="download-popup-content">
            <div className="spinner"></div>
            <p>{downloadMessage}</p>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

export default LoadStory

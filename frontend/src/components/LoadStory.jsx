import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import apiClient from '../services/api'
import './LoadStory.css'

function LoadStory({ onLoad, onBack }) {
  const [stories, setStories] = useState([])
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(null)
  const [downloadMessage, setDownloadMessage] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768)

  useEffect(() => {
    fetchStories()
    
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768)
    }
    
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const fetchStories = async () => {
    try {
      const response = await apiClient.get('/api/list-stories')
      console.log('Fetched stories:', response.data)
      console.log('First story details:', response.data[0])
      setStories(response.data)
    } catch (error) {
      console.error('Error fetching stories:', error)
      alert('Failed to load stories. Please refresh the page.')
    } finally {
      setLoading(false)
    }
  }
) => {
    try {
      console.log('Loading story with story_id:', story.story_id)
      console.log('Full story object:', story)
      const response = await apiClient.get(`/api/load-story/${story.story_id}`)
      console.log('Story loaded successfully:', response.data.name)
      onLoad(response.data.story_data, response.data.name, story.story_id)
    } catch (error) {
      console.error('Failed to load story:', error)
      const errorMsg = error.response?.data?.detail || error.message
      alert(`Failed to load story: ${errorMsg}\n\nStory ID: ${story.story_id || story.i
  const endIndex = startIndex + itemsPerPage
  const paginatedStories = filteredStories.slice(startIndex, endIndex)

  // Reset to page 1 when search changes
  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery])

  const handleLoad = async (storyId) => {
    try {
      console.log('Loading story with ID:', storyId)
      const response = await apiClient.get(`/api/load-story/${storyId}`)
      console.log('Story loaded successfully:', response.data.name)
      onLoad(response.data.story_data, response.data.name, storyId)
    } catch (error) {
      console.error('Failed to load story:', error)
      const errorMsg = error.response?.data?.detail || error.message
      alert(`Failed to load story: ${errorMsg}\n\nStory ID: ${storyId}`)
    }
  }
) => {
    if (!confirm(`Delete "${story.name}"? This cannot be undone.`)) return
    
    try {
      await apiClient.delete(`/api/delete-story/${story.story_id}`)
      setStories(stories.filter(s => s.story_id !== story.story_id))
    } catch (error) {
      alert('Failed to delete story: ' + error.message)
    }
  }

  const handleDownload = async (story) => {
    setDownloading(story.story_id)
    setDownloadMessage('Zipping file...')
    
    try {
      // Step 1: Request ZIP creation and download
      const response = await apiClient.get(`/api/export-story/${story.story_id}`, {
        responseType: 'blob'
      })
      
      // Step 2: Save
      setDownloadMessage('Saving file...')
      const url = window.URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = `${story.name.replace(/\s+/g, '_')}_${story.story_i
      link.download = `${storyName.replace(/\s+/g, '_')}_${storyId.substring(0, 8)}.zip`
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      // Step 3: Complete
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
        <>
          {/* Search Bar */}
          <div className="search-container">
            <input
              type="text"
              placeholder="🔍 Search stories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            {searchQuery && (
              <button 
                className="clear-search"
                onClick={() => setSearchQuery('')}
                title="Clear search"
              >
                ✕
              </button>
            )}
          </div>

          {/* Results Count */}
          {filteredStories.length > 0 && (
            <div className="results-info">
              Showing {startIndex + 1}-{Math.min(endIndex, filteredStories.length)} of {filteredStories.length} {filteredStories.length === 1 ? 'story' : 'stories'}
              {searchQuery && ` matching "${searchQuery}"`}
            </div>
          )}

          {filteredStories.length === 0 ? (
            <div className="no-stories">
              <p>🔍 No stories found matching "{searchQuery}"</p>
              <button onClick={() => setSearchQuery('')} className="clear-search-btn">
                Clear Search
              </button>
            </div>
          ) : (
            <>
              <div className="stories-grid">
                {paginatedStories.map((story) => (
                  <motion.div
                    key={story.story_id}
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
                        onClick={() => handleLoad(story)}
                      >
                        Load Story
                      </button>
                      <button 
                        className="download-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDownload(story)
                        }}
                        disabled={downloading !== null}
                        title="Download as ZIP file"
                      >
                        {downloading === story.story_id ? '⏳ Downloading...' : '⬇️ Download'}
                      </button>
                      <button 
                        className="delete-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(story)
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="pagination-controls">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="pagination-btn"
                  >
                    ← Previous
                  </button>
                  <span className="page-info">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="pagination-btn"
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </>
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

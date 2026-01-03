import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import JSZip from 'jszip'
import apiClient from '../services/api'
import * as storyStorage from '../utils/storyStorage'
import './OfflineManager.css'

function OfflineManager({ onLoadOffline, onBack }) {
  const [onlineStories, setOnlineStories] = useState([])
  const [localStories, setLocalStories] = useState([])
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [downloading, setDownloading] = useState(null)
  const [downloadMessage, setDownloadMessage] = useState('')
  const [storageInfo, setStorageInfo] = useState(null)

  const loadLocalStories = async () => {
    try {
      const stories = await storyStorage.listStories()
      setLocalStories(stories)
      
      // Get storage info
      const info = await storyStorage.getStorageInfo()
      setStorageInfo(info)
    } catch (error) {
      console.error('Failed to load local stories:', error)
    }
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
      const response = await apiClient.get('/api/list-stories')
      setOnlineStories(response.data)
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
      
      const result = await storyStorage.saveStory(localStory)
      setLocalStories(prev => [localStory, ...prev])
      
      console.log(`Story saved (${result.size.toFixed(2)}MB) to ${result.storage}`)
      return storyId
    } catch (error) {
      throw new Error('Failed to save locally: ' + error.message)
    }
  }

  const loadFromLocal = async (storyId) => {
    try {
      const storyData = await storyStorage.loadStory(storyId)
      if (storyData) {
        onLoadOffline(storyData.storyData, storyData.name)
      } else {
        alert('Story not found')
      }
    } catch (error) {
      alert('Failed to load story: ' + error.message)
    }
  }

  const deleteLocal = async (storyId) => {
    if (!confirm('Delete this local story?')) return
    
    try {
      await storyStorage.deleteStory(storyId)
      setLocalStories(prev => prev.filter(s => s.id !== storyId))
      await loadLocalStories() // Refresh storage info
    } catch (error) {
      alert('Failed to delete story: ' + error.message)
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
      const response = await apiClient.get(`/api/export-story/${storyId}`, {
        responseType: 'blob'
      })
      
      // Step 2: Save
      setDownloadMessage('Saving file...')
      const blob = response.data
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
    
    setDownloading('import')
    setDownloadMessage('Extracting ZIP file...')
    
    try {
      // Load ZIP file
      const zip = new JSZip()
      const zipData = await zip.loadAsync(file)
      
      // Try to read story.json (new format from export)
      let storyData = null
      const storyFile = zipData.file('story.json')
      
      if (storyFile) {
        // New format: story.json with embedded structure
        setDownloadMessage('Reading story data...')
        const storyText = await storyFile.async('string')
        storyData = JSON.parse(storyText)
      } else {
        // Old format: metadata.json + story_data.json
        const metadataFile = zipData.file('metadata.json')
        if (!metadataFile) {
          throw new Error('Invalid story package: missing story.json or metadata.json')
        }
        
        setDownloadMessage('Reading story data...')
        const metadataText = await metadataFile.async('string')
        const metadata = JSON.parse(metadataText)
        
        const storyDataFile = zipData.file('story_data.json')
        if (!storyDataFile) {
          throw new Error('Invalid story package: missing story_data.json')
        }
        
        const storyDataText = await storyDataFile.async('string')
        storyData = JSON.parse(storyDataText)
      }
      
      setDownloadMessage('Converting media to base64...')
      
      // Convert all scene images and audio to base64 data URLs
      for (let i = 0; i < storyData.scenes.length; i++) {
        const scene = storyData.scenes[i]
        
        // Convert image to base64
        if (scene.image_url) {
          const imagePath = scene.image_url.replace('/media/', '')
          const imageFile = zipData.file(imagePath)
          if (imageFile) {
            // Detect image MIME type from file extension
            const imageExt = imagePath.split('.').pop().toLowerCase()
            const mimeTypes = {
              'jpg': 'image/jpeg',
              'jpeg': 'image/jpeg',
              'png': 'image/png',
              'gif': 'image/gif',
              'webp': 'image/webp',
              'svg': 'image/svg+xml'
            }
            const imageMimeType = mimeTypes[imageExt] || 'image/png'
            
            const imageBlob = await imageFile.async('blob')
            // Create blob with correct MIME type
            const typedImageBlob = new Blob([imageBlob], { type: imageMimeType })
            const imageDataUrl = await new Promise((resolve) => {
              const reader = new FileReader()
              reader.onloadend = () => resolve(reader.result)
              reader.readAsDataURL(typedImageBlob)
            })
            scene.image_url = imageDataUrl
          }
        }
        
        // Convert audio to base64
        if (scene.audio_url) {
          const audioPath = scene.audio_url.replace('/media/', '')
          const audioFile = zipData.file(audioPath)
          if (audioFile) {
            // Detect audio MIME type from file extension
            const audioExt = audioPath.split('.').pop().toLowerCase()
            const mimeTypes = {
              'mp3': 'audio/mpeg',
              'wav': 'audio/wav',
              'ogg': 'audio/ogg',
              'webm': 'audio/webm',
              'm4a': 'audio/mp4',
              'aac': 'audio/aac'
            }
            const audioMimeType = mimeTypes[audioExt] || 'audio/mpeg'
            
            const audioBlob = await audioFile.async('blob')
            // Create blob with correct MIME type
            const typedAudioBlob = new Blob([audioBlob], { type: audioMimeType })
            const audioDataUrl = await new Promise((resolve) => {
              const reader = new FileReader()
              reader.onloadend = () => resolve(reader.result)
              reader.readAsDataURL(typedAudioBlob)
            })
            scene.audio_url = audioDataUrl
          }
        }
      }
      
      setDownloadMessage('Saving to storage...')
      
      // Save using storyStorage (auto-selects IndexedDB or localStorage)
      const localStoryId = `local_${Date.now()}`
      const localStory = {
        id: localStoryId,
        name: storyData.title || 'Imported Story',
        storyData: storyData,
        savedAt: Date.now(),
        isOffline: true
      }
      
      const result = await storyStorage.saveStory(localStory)
      console.log(`Story imported (${result.size.toFixed(2)}MB) to ${result.storage}`)
      
      setDownloadMessage('Complete! ✓')
      
      // Navigate to story player after brief delay
      setTimeout(() => {
        setDownloadMessage('')
        setDownloading(null)
        onLoadOffline(storyData, localStory.name)
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
        <div className="header-info">
          <div className={`connection-status ${isOnline ? 'online' : 'offline'}`}>
            {isOnline ? '🟢 Online' : '🔴 Offline'}
          </div>
          {storageInfo && (
            <div className="storage-info">
              💾 {storageInfo.usage}MB / {storageInfo.quota}MB used
            </div>
          )}
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

      <div className="offline-footer">
        <button className="back-btn" onClick={onBack}>
          ← Back to Home
        </button>
      </div>

      <AnimatePresence>
        {downloadMessage && (
          <div className="download-popup">
            <motion.div 
              className="download-popup-content"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
            >
              <div>
                <div className="spinner"></div>
              </div>
              <p>{downloadMessage}</p>
              
              {/* Progress Bar */}
              <div className="progress-bar-container">
                <div 
                  className="progress-bar"
                  style={{
                    width: downloadMessage.includes('Uploading') || downloadMessage.includes('Zipping') || downloadMessage.includes('Extracting') ? '25%' : 
                           downloadMessage.includes('Downloading') || downloadMessage.includes('Reading') ? '60%' : 
                           downloadMessage.includes('Saving') || downloadMessage.includes('Converting') ? '85%' : '100%',
                    transition: 'width 0.4s ease'
                  }}
                ></div>
              </div>
              
              {/* Step Indicators */}
              <div className="progress-steps">
                <div className={`progress-step ${(downloadMessage.includes('Uploading') || downloadMessage.includes('Zipping') || downloadMessage.includes('Extracting')) ? 'active' : (downloadMessage.includes('Downloading') || downloadMessage.includes('Reading') || downloadMessage.includes('Saving') || downloadMessage.includes('Converting') || downloadMessage === 'Complete! ✓') ? 'completed' : ''}`}>
                  <div className="step-dot">1</div>
                  <span>{downloadMessage.includes('Uploading') ? 'Upload' : downloadMessage.includes('Extracting') ? 'Extract' : 'Zip'}</span>
                </div>
                <div className={`progress-step ${(downloadMessage.includes('Downloading') || downloadMessage.includes('Reading')) ? 'active' : (downloadMessage.includes('Saving') || downloadMessage.includes('Converting') || downloadMessage === 'Complete! ✓') ? 'completed' : ''}`}>
                  <div className="step-dot">2</div>
                  <span>{downloadMessage.includes('Reading') ? 'Read' : 'Download'}</span>
                </div>
                <div className={`progress-step ${(downloadMessage.includes('Saving') || downloadMessage.includes('Converting')) ? 'active' : downloadMessage === 'Complete! ✓' ? 'completed' : ''}`}>
                  <div className="step-dot">3</div>
                  <span>{downloadMessage.includes('Converting') ? 'Convert' : 'Save'}</span>
                </div>
                <div className={`progress-step ${downloadMessage === 'Complete! ✓' ? 'completed' : ''}`}>
                  <div className="step-dot">✓</div>
                  <span>Done</span>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default OfflineManager

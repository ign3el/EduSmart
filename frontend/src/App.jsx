import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import FileUpload from './components/FileUpload'
import FileConfirmation from './components/FileConfirmation'
import AvatarSelector from './components/AvatarSelector'
import StoryPlayer from './components/StoryPlayer'
import SaveStoryModal from './components/SaveStoryModal'
import LoadStory from './components/LoadStory'
import OfflineManager from './components/OfflineManager'
import ReuploadConfirmModal from './components/ReuploadConfirmModal'
import UploadProgressOverlay from './components/UploadProgressOverlay'
import './App.css'

function App() {
  const [step, setStep] = useState('home') 
  const [uploadedFile, setUploadedFile] = useState(null)
  const [selectedAvatar, setSelectedAvatar] = useState(null)
  const [selectedVoice, setSelectedVoice] = useState('en-US-JennyNeural')
  const [storyData, setStoryData] = useState(null)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [gradeLevel, setGradeLevel] = useState(3)
  const [currentJobId, setCurrentJobId] = useState(null)
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [isSaved, setIsSaved] = useState(false)
  const [isOfflineMode, setIsOfflineMode] = useState(false)
  const [showReuploadModal, setShowReuploadModal] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadFileName, setUploadFileName] = useState('')
  const [showUploadProgress, setShowUploadProgress] = useState(false)

  const previousStep = (current) => {
    switch (current) {
      case 'playing':
      case 'generating':
        return 'avatar'
      case 'avatar':
        return 'confirm'
      case 'confirm':
        return 'upload'
      case 'upload':
      case 'offline':
      case 'load':
      default:
        return 'home'
    }
  }

  // Handle browser back button to navigate within app steps
  useEffect(() => {
    const handlePopState = (event) => {
      event.preventDefault()
      const prev = previousStep(step)
      setStep(prev)
      window.history.pushState({ step: prev }, '')
    }

    window.history.pushState({ step }, '')
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [step])

  const handleFileUpload = (file) => {
    setUploadFileName(file.name)
    setShowUploadProgress(true)
    setUploadProgress(0)
    
    // Simulate upload progress
    let progress = 0
    const interval = setInterval(() => {
      progress += Math.random() * 30
      if (progress >= 90) progress = 90
      setUploadProgress(Math.round(progress))
    }, 300)
    
    // Complete upload
    setTimeout(() => {
      clearInterval(interval)
      setUploadProgress(100)
      
      // Proceed after completion
      setTimeout(() => {
        setShowUploadProgress(false)
        setUploadedFile(file)
        setStep('confirm')
        setError(null) 
        setIsSaved(false)
      }, 800)
    }, 2000)
  }

  const handleReuploadClick = () => {
    setShowReuploadModal(true)
  }

  const handleReuploadConfirm = () => {
    setShowReuploadModal(false)
    setUploadedFile(null)
    setSelectedAvatar(null)
    setStoryData(null)
    setStep('upload')
  }

  const handleAvatarSelect = async (avatar) => {
    setSelectedAvatar(avatar)
    await generateStory(avatar)
  }

  const generateStory = async (avatar) => {
    try {
      setStep('generating')
      setError(null)
      setProgress(0)
      setIsSaved(false)

      const formData = new FormData()
      formData.append('file', uploadedFile)
      formData.append('grade_level', gradeLevel)
      formData.append('avatar_type', avatar.id)
      formData.append('voice', selectedVoice)  // Send selected voice to backend

      const response = await fetch('/api/upload', { method: 'POST', body: formData })
      
      if (!response.ok) throw new Error("Failed to start story generation.")
      
      const { job_id } = await response.json()
      setCurrentJobId(job_id)

      // Polling Loop
      const pollTimer = setInterval(async () => {
        try {
          const statusRes = await fetch(`/api/status/${job_id}`)
          if (!statusRes.ok) throw new Error("Could not fetch status")
          
          const job = await statusRes.json()

          if (job.status === 'processing') {
            setProgress((prev) => Math.max(prev, job.progress ?? prev))
          } else if (job.status === 'completed') {
            clearInterval(pollTimer)
            setStoryData(job.result)
            setProgress(100)
            setStep('playing')
          } else if (job.status === 'failed') {
            clearInterval(pollTimer)
            throw new Error(job.error || "AI Generation failed.")
          }
        } catch (err) {
          clearInterval(pollTimer)
          setError("Connection lost: " + err.message)
          setStep('upload')
        }
      }, 2000)

    } catch (err) {
      setError(err.message)
      setStep('upload')
    }
  }

  const handleRestart = async () => {
    // Cleanup unsaved story
    if (currentJobId && !isSaved) {
      try {
        await fetch(`/api/cleanup/${currentJobId}`, { method: 'DELETE' })
      } catch (error) {
        console.error('Cleanup failed:', error)
      }
    }
    
    setStep('home')
    setUploadedFile(null)
    setSelectedAvatar(null)
    setStoryData(null)
    setError(null)
    setProgress(0)
    setCurrentJobId(null)
    setIsSaved(false)
    setIsOfflineMode(false)
  }

  const handleSaveStory = () => {
    setShowSaveModal(true)
  }

  const handleSaveComplete = async (storyId, storyName) => {
    setShowSaveModal(false)
    setIsSaved(true)
    alert(`✅ Story "${storyName}" saved successfully!`)
  }

  const handleLoadOffline = (loadedStoryData, storyName) => {
    setStoryData(loadedStoryData)
    setSelectedAvatar({ id: 'offline', name: 'Offline Story' })
    setIsSaved(true)
    setIsOfflineMode(true)
    setStep('playing')
  }

  const handleSaveOffline = async (storyData, storyName) => {
    try {
      // Save to localStorage
      const storyId = `local_${Date.now()}`
      const localStory = {
        id: storyId,
        name: storyName,
        storyData: storyData,
        savedAt: Date.now(),
        isOffline: true
      }
      
      localStorage.setItem(`edusmart_story_${storyId}`, JSON.stringify(localStory))
      alert(`✅ Story "${storyName}" saved locally!`)
      return storyId
    } catch (error) {
      throw new Error('Failed to save locally: ' + error.message)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>📚 EduSmart</h1>
        <p>Transform learning into an adventure!</p>
      </header>

      <main className="app-main">
        {error && (
          <div className="error-message">
            <p>⚠️ {error}</p>
            <button onClick={() => setError(null)}>Try Again</button>
          </div>
        )}
        
        <AnimatePresence mode="wait">
          {step === 'home' && (
            <motion.div key="home" className="home-container">
              <div className="home-buttons">
                <motion.button 
                  className="home-btn create-btn"
                  onClick={() => setStep('upload')}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  ✨ Create New Story
                </motion.button>
                <motion.button 
                  className="home-btn load-btn"
                  onClick={() => setStep('load')}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  📚 Load Online Story
                </motion.button>
                <motion.button 
                  className="home-btn offline-btn"
                  onClick={() => setStep('offline')}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  📱 Offline Manager
                </motion.button>
              </div>
            </motion.div>
          )}

          {step === 'upload' && (
            <motion.div key="upload" className="step-container">
              <FileUpload 
                onUpload={handleFileUpload}
                gradeLevel={gradeLevel}
                onGradeLevelChange={setGradeLevel}
              />
              <button className="back-to-home-btn" onClick={() => setStep('home')}>
                ← Back to Home
              </button>
            </motion.div>
          )}

          {step === 'confirm' && (
            <motion.div key="confirm" className="step-container">
              <FileConfirmation
                file={uploadedFile}
                gradeLevel={gradeLevel}
                onConfirm={handleConfirmFile}
                onBack={() => setStep('upload')}
                onReupload={handleReuploadClick}
                onEditGrade={(newGrade) => setGradeLevel(newGrade)}
              />
            </motion.div>
          )}

          {step === 'offline' && (
            <motion.div key="offline" className="step-container">
              <OfflineManager 
                onLoadOffline={handleLoadOffline}
                onBack={() => setStep('home')}
              />
            </motion.div>
          )}

          {step === 'load' && (
            <motion.div key="load" className="step-container">
              <LoadStory 
                onLoad={(storyData, storyName) => {
                  setStoryData(storyData)
                  setSelectedAvatar({ id: 'loaded', name: 'Saved Story' })
                  setIsSaved(true)
                  setStep('playing')
                }}
                onBack={() => setStep('home')}
              />
            </motion.div>
          )}

          {step === 'avatar' && (
            <motion.div key="avatar" className="step-container">
              <AvatarSelector onSelect={handleAvatarSelect} />
            </motion.div>
          )}

          {step === 'generating' && (
            <motion.div key="generating" className="generating-container">
              <div className="loading-spinner"></div>
              <h2>Creating Your Story...</h2>
              
              <div className="progress-container">
                <div className="progress-bar-bg">
                  <motion.div 
                    className="progress-bar-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                <p>{progress}% Complete</p>
              </div>
              
              <p className="small-text">Generating custom images and voiceovers...</p>
            </motion.div>
          )}

          {step === 'playing' && storyData && (
            <motion.div key="playing" className="player-container">
              <StoryPlayer 
                storyData={storyData} 
                avatar={selectedAvatar} 
                onRestart={handleRestart}
                onSave={handleSaveStory}
                isSaved={isSaved}
                isOffline={isOfflineMode}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {showSaveModal && (
          <SaveStoryModal 
            jobId={currentJobId}
            onSave={handleSaveComplete}
            onCancel={() => setShowSaveModal(false)}
          />
        )}

        {showReuploadModal && (
          <ReuploadConfirmModal
            onConfirm={handleReuploadConfirm}
            onCancel={() => setShowReuploadModal(false)}
          />
        )}

        {showUploadProgress && (
          <UploadProgressOverlay
            progress={uploadProgress}
            fileName={uploadFileName}
            isVisible={showUploadProgress}
          />
        )}
      </main>
    </div>
  )
}

export default App
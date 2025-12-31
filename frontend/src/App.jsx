import { useState, useEffect, useRef } from 'react'
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
  const [savedStoryId, setSavedStoryId] = useState(null)
  const [isOfflineMode, setIsOfflineMode] = useState(false)
  const [showReuploadModal, setShowReuploadModal] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadFileName, setUploadFileName] = useState('')
  const [showUploadProgress, setShowUploadProgress] = useState(false)
  const fileInputRef = useRef(null)

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
    setUploadedFile(file)
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
    // Trigger hidden file input instead of navigating
    if (fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  const handleFileInputChange = (e) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleConfirmFile = (voice) => {
    if (voice) {
      setSelectedVoice(voice)
    }
    setStep('avatar')
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
    setSavedStoryId(null)
    setIsOfflineMode(false)
  }

  const handleSaveStory = () => {
    setShowSaveModal(true)
  }

  const handleSaveComplete = async (storyId, storyName) => {
    setShowSaveModal(false)
    setIsSaved(true)
    setSavedStoryId(storyId)
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
        <div className="app-header-content">
          <h1>EduSmart — AI Storymaker</h1>
          <p>Transform your PDFs or DOCX files into animated, voice-guided adventures tailored for every grade.</p>
        </div>
      </header>

      <main className="app-main">
        <div className="content-shell">
          {error && (
            <div className="error-message">
              <p>⚠️ {error}</p>
              <button onClick={() => setError(null)}>Try Again</button>
            </div>
          )}
          
          <AnimatePresence mode="wait">
            {step === 'home' && (
              <motion.div key="home" className="home-container">
                <div className="home-topline">
                  <h2>Choose how you want to begin</h2>
                  <span className="pill">Smart, fast, and offline-ready</span>
                </div>
                <div className="home-buttons">
                  <motion.button 
                    className="home-btn create-btn"
                    onClick={() => setStep('upload')}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <div className="emoji">✨</div>
                    <strong>Create New Story</strong>
                    <span>Upload a lesson file and let AI turn it into a story</span>
                  </motion.button>
                  <motion.button 
                    className="home-btn load-btn"
                    onClick={() => setStep('load')}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <div className="emoji">📚</div>
                    <strong>Load Online Story</strong>
                    <span>Pull down a saved adventure from the cloud</span>
                  </motion.button>
                  <motion.button 
                    className="home-btn offline-btn"
                    onClick={() => setStep('offline')}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <div className="emoji">📱</div>
                    <strong>Offline Manager</strong>
                    <span>Manage locally stored stories without an internet connection</span>
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
                onLoad={(storyData, storyName, storyId) => {
                  setStoryData(storyData)
                  setSelectedAvatar({ id: 'loaded', name: 'Saved Story' })
                  setIsSaved(true)
                  setSavedStoryId(storyId)
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
                savedStoryId={savedStoryId}
                currentJobId={currentJobId}
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

          {/* Hidden file input for re-upload */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc"
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
          />
        </div>
      </main>
    </div>
  )
}

export default App
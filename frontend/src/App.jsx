import { useState, useEffect } from 'react' // <--- MUST include useEffect
import { motion, AnimatePresence } from 'framer-motion'
import FileUpload from './components/FileUpload'
import AvatarSelector from './components/AvatarSelector'
import StoryPlayer from './components/StoryPlayer'
import SaveStoryModal from './components/SaveStoryModal'
import LoadStory from './components/LoadStory'
import './App.css'

function App() {
  const [step, setStep] = useState('home') 
  const [uploadedFile, setUploadedFile] = useState(null)
  const [selectedAvatar, setSelectedAvatar] = useState(null)
  const [storyData, setStoryData] = useState(null)
  const [progress, setProgress] = useState(0) // <--- Check if this exists
  const [error, setError] = useState(null)
  const [gradeLevel, setGradeLevel] = useState(3)
  const [currentJobId, setCurrentJobId] = useState(null)
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [isSaved, setIsSaved] = useState(false)

  const handleFileUpload = (file) => {
    setUploadedFile(file)
    setStep('avatar')
    setError(null) 
    setIsSaved(false)
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
            setProgress(job.progress)
          } else if (job.status === 'completed') {
            clearInterval(pollTimer)
            setStoryData(job.result)
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
  }

  const handleSaveStory = () => {
    setShowSaveModal(true)
  }

  const handleSaveComplete = async (storyId, storyName) => {
    setShowSaveModal(false)
    setIsSaved(true)
    alert(`✅ Story "${storyName}" saved successfully!`)
  }

  const handleLoadStory = (loadedStoryData, storyName) => {
    setStoryData(loadedStoryData)
    setSelectedAvatar({ id: 'loaded', name: 'Saved Story' })
    setIsSaved(true)
    setStep('playing')
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
                  📚 Load Saved Story
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

          {step === 'load' && (
            <motion.div key="load" className="step-container">
              <LoadStory 
                onLoad={handleLoadStory}
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
      </main>
    </div>
  )
}

export default App
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import FileUpload from './components/FileUpload'
import AvatarSelector from './components/AvatarSelector'
import StoryPlayer from './components/StoryPlayer'
import './App.css'

function App() {
  const [step, setStep] = useState('upload') 
  const [uploadedFile, setUploadedFile] = useState(null)
  const [selectedAvatar, setSelectedAvatar] = useState(null)
  const [storyData, setStoryData] = useState(null)
  const [progress, setProgress] = useState(0) // New state for progress bar
  const [error, setError] = useState(null)

  const generateStory = async (avatar) => {
    try {
      setStep('generating')
      setError(null)
      setProgress(0)

      const formData = new FormData()
      formData.append('file', uploadedFile)

      // 1. Trigger the background job
      const response = await fetch('/api/upload', { method: 'POST', body: formData })
      if (!response.ok) throw new Error("Failed to start story generation.")
      const { job_id } = await response.json()

      // 2. Polling Loop
      const pollTimer = setInterval(async () => {
        try {
          const statusRes = await fetch(`/api/status/${job_id}`)
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
          setError(err.message)
          setStep('upload')
        }
      }, 2000) // Poll every 2 seconds

    } catch (err) {
      setError(err.message)
      setStep('upload')
    }
  }

  return (
    <div className="app">
      {/* ... (Existing Header) ... */}
      <main className="app-main">
        {error && <div className="error-message">⚠️ {error}</div>}
        
        <AnimatePresence mode="wait">
          {/* ... (Existing Upload/Avatar Steps) ... */}

          {step === 'generating' && (
            <motion.div key="generating" className="generating-container">
              <div className="loading-spinner"></div>
              <h2>Creating Your Story...</h2>
              
              {/* Progress Bar UI */}
              <div className="progress-container">
                <div className="progress-bar-bg">
                  <motion.div 
                    className="progress-bar-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                  />
                </div>
                <p>{progress}% Complete</p>
              </div>
              
              <p>Crafting custom images and voiceovers...</p>
            </motion.div>
          )}

          {step === 'playing' && storyData && (
            <StoryPlayer storyData={storyData} avatar={selectedAvatar} onRestart={() => setStep('upload')} />
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}

export default App
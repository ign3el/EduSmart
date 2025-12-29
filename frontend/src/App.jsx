import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import FileUpload from './components/FileUpload'
import AvatarSelector from './components/AvatarSelector'
import StoryPlayer from './components/StoryPlayer'
import './App.css'

function App() {
  const [step, setStep] = useState('upload') // upload, avatar, generating, playing
  const [uploadedFile, setUploadedFile] = useState(null)
  const [selectedAvatar, setSelectedAvatar] = useState(null)
  const [storyData, setStoryData] = useState(null)
  const [gradeLevel, setGradeLevel] = useState(3)
  const [error, setError] = useState(null)

  const handleFileUpload = (file) => {
    setUploadedFile(file)
    setStep('avatar')
    setError(null) 
  }

  const handleAvatarSelect = async (avatar) => {
    setSelectedAvatar(avatar)
    await generateStory(avatar)
  }

  const generateStory = async (avatar) => {
    try {
      setStep('generating')
      setError(null)

      const formData = new FormData()
      formData.append('file', uploadedFile)
      formData.append('grade_level', gradeLevel)
      formData.append('avatar_type', avatar.id)

      // The AI generation can take 2+ minutes, so we use a long-lived fetch
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      // --- SAFETY FIXES START ---
      
      // 1. Check for Server/Proxy Errors (524, 499, 504)
      if (!response.ok) {
        if (response.status === 524) {
          throw new Error("AI Timeout (Cloudflare 524): The generation took longer than 100 seconds. Please disable Cloudflare Proxy (Grey Cloud) for edusmart.ign3el.com.");
        }
        if (response.status === 499 || response.status === 504) {
          throw new Error("Server Timeout: Nginx closed the connection. Please verify proxy_read_timeout is set to 300s in aaPanel.");
        }
        throw new Error(`Server Error (${response.status}): The backend failed to complete the story.`);
      }

      // 2. Content-Type Guard: Prevent "Unexpected token '<'" error
      // This ensures we don't try to parse HTML error pages as JSON
      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        const errorHtml = await response.text();
        console.error("Non-JSON Response received:", errorHtml);
        throw new Error("Invalid Response: The server returned an error page instead of story data. This usually indicates a timeout.");
      }

      const data = await response.json()
      
      // 3. Data Integrity Check
      if (!data.scenes || data.scenes.length === 0) {
        throw new Error("The AI generated an empty story. Please try again with a different file.");
      }

      // --- SAFETY FIXES END ---

      setStoryData(data)
      setStep('playing')
    } catch (err) {
      console.error('Generation Failed:', err)
      setError(err.message || "An unexpected error occurred during generation.")
      setStep('upload') // Reset to allow retry
    }
  }

  const handleRestart = () => {
    setStep('upload')
    setUploadedFile(null)
    setSelectedAvatar(null)
    setStoryData(null)
    setError(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>📚 EduSmart</h1>
        <p>Transform learning into an adventure!</p>
      </header>

      <main className="app-main">
        {error && (
          <motion.div 
            className="error-message"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <p>⚠️ {error}</p>
            <button onClick={() => setError(null)}>Try Again</button>
          </motion.div>
        )}
        
        <AnimatePresence mode="wait">
          {step === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="step-container"
            >
              <FileUpload 
                onUpload={handleFileUpload}
                gradeLevel={gradeLevel}
                onGradeLevelChange={setGradeLevel}
              />
            </motion.div>
          )}

          {step === 'avatar' && (
            <motion.div
              key="avatar"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="step-container"
            >
              <AvatarSelector onSelect={handleAvatarSelect} />
            </motion.div>
          )}

          {step === 'generating' && (
            <motion.div
              key="generating"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="generating-container"
            >
              <div className="loading-spinner"></div>
              <h2>Creating Your Story...</h2>
              <p>Our AI is crafting an amazing learning experience!</p>
              <p className="small-text">This usually takes about 60-120 seconds because we are generating custom images and audio for you.</p>
            </motion.div>
          )}

          {step === 'playing' && storyData && (
            <motion.div
              key="playing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="player-container"
            >
              <StoryPlayer 
                storyData={storyData}
                avatar={selectedAvatar}
                onRestart={handleRestart}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}

export default App
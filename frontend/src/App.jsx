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

      // ACTION: We only need ONE call because the backend handles 
      // extraction, image gen, and audio gen in the upload route.
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Server error: ${response.statusText}`)
      }

      const data = await response.json()

      // FIX: Ensure the backend returned 'scenes'
      if (!data || !data.scenes || data.scenes.length === 0) {
        throw new Error("The AI didn't generate any scenes. Please try a different file.")
      }

      // Add the VPS domain to URLs if the backend only sends relative paths
      const formattedStory = {
        ...data,
        scenes: data.scenes.map(scene => ({
          ...scene,
          image_url: scene.image_url ? `https://edusmart.ign3el.com${scene.image_url}` : null,
          audio_url: scene.audio_url ? `https://edusmart.ign3el.com${scene.audio_url}` : null
        }))
      }

      setStoryData(formattedStory)
      setStep('playing')
    } catch (err) {
      console.error('Error generating story:', err)
      setError(err.message || 'Failed to generate the story. Please try again.')
      setStep('upload') 
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
              <p className="small-text">This usually takes about 30-60 seconds.</p>
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
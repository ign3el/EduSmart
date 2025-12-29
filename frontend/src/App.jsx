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
    setError(null) // Clear previous errors
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

      const uploadResponse = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.statusText}`)
      }
      const uploadData = await uploadResponse.json()

      const storyResponse = await fetch(`/api/generate-story/${uploadData.story_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_text: uploadData.extracted_text || '',
          grade_level: gradeLevel,
          avatar_type: avatar.id,
          style: 'anime'
        }),
      })

      if (!storyResponse.ok) {
        throw new Error(`Story generation failed: ${storyResponse.statusText}`)
      }
      const story = await storyResponse.json()

      setStoryData(story)
      setStep('playing')
    } catch (err) {
      console.error('Error generating story:', err)
      setError('Failed to generate the story. Please check the file or try again later.')
      setStep('upload') // Go back to the upload step on error
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
            <p>{error}</p>
            <button onClick={() => setError(null)}>Dismiss</button>
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

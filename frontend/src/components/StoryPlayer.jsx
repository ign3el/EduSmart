import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FiPlay, FiPause, FiSkipForward, FiSkipBack, FiRotateCw } from 'react-icons/fi'
import './StoryPlayer.css'

function StoryPlayer({ storyData, avatar, onRestart }) {
  const [currentScene, setCurrentScene] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const audioRef = useRef(null)

  const scenes = storyData.timeline.scenes || []
  const scene = scenes[currentScene]

  useEffect(() => {
    if (isPlaying && scene) {
      const duration = scene.duration * 1000 // Convert to milliseconds
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            goToNextScene()
            return 0
          }
          return prev + (100 / duration) * 100
        })
      }, 100)

      return () => clearInterval(interval)
    }
  }, [isPlaying, currentScene, scene])

  const goToNextScene = () => {
    if (currentScene < scenes.length - 1) {
      setCurrentScene(currentScene + 1)
      setProgress(0)
    } else {
      setIsPlaying(false)
      setProgress(0)
    }
  }

  const goToPrevScene = () => {
    if (currentScene > 0) {
      setCurrentScene(currentScene - 1)
      setProgress(0)
    }
  }

  const togglePlay = () => {
    setIsPlaying(!isPlaying)
  }

  if (!scene) {
    return <div>Loading story...</div>
  }

  return (
    <div className="story-player">
      <div className="player-header">
        <h2>🎬 {avatar.name}'s Story Time</h2>
        <button className="restart-btn" onClick={onRestart}>
          <FiRotateCw /> New Story
        </button>
      </div>

      <div className="scene-display">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentScene}
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -100 }}
            transition={{ duration: 0.5 }}
            className="scene-content"
          >
            {/* Scene Image */}
            <div className="scene-image">
              {scene.image && !scene.image.includes('placeholder') ? (
                <img src={scene.image} alt={`Scene ${currentScene + 1}`} />
              ) : (
                <div className="placeholder-image">
                  <span className="avatar-large">{avatar.emoji}</span>
                  <p>{scene.visual_description}</p>
                </div>
              )}
            </div>

            {/* Scene Narration */}
            <div className="scene-narration">
              <div className="narrator-badge">
                <span>{avatar.emoji}</span>
                <span>{avatar.name}</span>
              </div>
              <p className="narration-text">{scene.narration}</p>
              
              {scene.learning_point && (
                <div className="learning-point">
                  <span className="lightbulb">💡</span>
                  <span>{scene.learning_point}</span>
                </div>
              )}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Progress Bar */}
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Controls */}
      <div className="player-controls">
        <div className="scene-counter">
          Scene {currentScene + 1} of {scenes.length}
        </div>

        <div className="control-buttons">
          <button 
            onClick={goToPrevScene} 
            disabled={currentScene === 0}
            className="control-btn"
          >
            <FiSkipBack />
          </button>

          <button 
            onClick={togglePlay}
            className="control-btn play-btn"
          >
            {isPlaying ? <FiPause /> : <FiPlay />}
          </button>

          <button 
            onClick={goToNextScene}
            disabled={currentScene === scenes.length - 1}
            className="control-btn"
          >
            <FiSkipForward />
          </button>
        </div>

        <div className="scene-dots">
          {scenes.map((_, index) => (
            <button
              key={index}
              className={`dot ${index === currentScene ? 'active' : ''} ${index < currentScene ? 'completed' : ''}`}
              onClick={() => {
                setCurrentScene(index)
                setProgress(0)
              }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export default StoryPlayer

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiPlay, FiPause, FiSkipForward, FiSkipBack, FiRotateCw } from 'react-icons/fi';
import './StoryPlayer.css';

function StoryPlayer({ storyData, avatar, onRestart }) {
  const [currentScene, setCurrentScene] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const audioRef = useRef(null);

  const scenes = storyData.timeline.scenes || [];
  const scene = scenes[currentScene];

  // Effect to control audio playback (play/pause)
  useEffect(() => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.play().catch(err => console.error("Audio play failed:", err));
      } else {
        audioRef.current.pause();
      }
    }
  }, [isPlaying, currentScene]); // Rerun when scene changes to load new audio

  // Effect to handle scene changes and audio loading
  useEffect(() => {
    setProgress(0);
    if (audioRef.current) {
      audioRef.current.src = scene?.audio || '';
      if (isPlaying) {
        audioRef.current.play().catch(err => console.error("Audio play failed on scene change:", err));
      }
    }
  }, [currentScene, scene?.audio]);

  const goToNextScene = () => {
    if (currentScene < scenes.length - 1) {
      setCurrentScene(currentScene + 1);
    } else {
      setIsPlaying(false); // Story finished
    }
  };

  const goToPrevScene = () => {
    if (currentScene > 0) {
      setCurrentScene(currentScene - 1);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      const newProgress = (audioRef.current.currentTime / audioRef.current.duration) * 100;
      setProgress(newProgress);
    }
  };
  
  const handleAudioEnded = () => {
    goToNextScene();
  };

  const handleDotClick = (index) => {
    setCurrentScene(index);
  };

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  if (!scene) {
    return (
      <div className="story-player">
        <p>Story has finished or is loading!</p>
        <button className="restart-btn" onClick={onRestart}>
          <FiRotateCw /> New Story
        </button>
      </div>
    );
  }

  return (
    <div className="story-player">
      <audio
        ref={audioRef}
        src={scene.audio}
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleAudioEnded}
        // preload="auto"
      />
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
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.5 }}
            className="scene-content"
          >
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

      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      <div className="player-controls">
        <div className="scene-counter">
          Scene {currentScene + 1} of {scenes.length}
        </div>
        <div className="control-buttons">
          <button onClick={goToPrevScene} disabled={currentScene === 0} className="control-btn"><FiSkipBack /></button>
          <button onClick={togglePlay} className="control-btn play-btn">{isPlaying ? <FiPause /> : <FiPlay />}</button>
          <button onClick={goToNextScene} disabled={currentScene === scenes.length - 1} className="control-btn"><FiSkipForward /></button>
        </div>
        <div className="scene-dots">
          {scenes.map((_, index) => (
            <button
              key={`dot-${index}`}
              className={`dot ${index === currentScene ? 'active' : ''} ${index < currentScene ? 'completed' : ''}`}
              onClick={() => handleDotClick(index)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default StoryPlayer;
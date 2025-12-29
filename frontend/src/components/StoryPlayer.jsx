import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiPlay, FiPause, FiSkipForward, FiSkipBack, FiRotateCw } from 'react-icons/fi';
import './StoryPlayer.css';

const API_DOMAIN = "https://edusmart.ign3el.com";

function StoryPlayer({ storyData, avatar, onRestart }) {
  const [currentScene, setCurrentScene] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const audioRef = useRef(null);

  const scenes = storyData?.scenes || [];
  const scene = scenes[currentScene];

  const fullAudioUrl = scene?.audio_url ? `${API_DOMAIN}${scene.audio_url}` : '';
  const fullImageUrl = scene?.image_url ? `${API_DOMAIN}${scene.image_url}` : '';

  useEffect(() => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.play().catch(err => console.error("Audio play failed:", err));
      } else {
        audioRef.current.pause();
      }
    }
  }, [isPlaying, currentScene]);

  useEffect(() => {
    setProgress(0);
    if (audioRef.current) {
      audioRef.current.src = fullAudioUrl;
      audioRef.current.load(); // Important to load the new source
      if (isPlaying) {
        audioRef.current.play().catch(err => console.error("Audio play failed on scene change:", err));
      }
    }
  }, [currentScene, fullAudioUrl]);

  const goToNextScene = () => {
    if (currentScene < scenes.length - 1) {
      setCurrentScene(currentScene + 1);
    } else {
      setIsPlaying(false);
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
        src={fullAudioUrl}
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleAudioEnded}
        preload="auto"
      />
      <div className="player-header">
        <h2>🎬 {storyData.title || "Story Time"}</h2>
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
              {fullImageUrl ? (
                <img src={fullImageUrl} alt={`Scene ${currentScene + 1}`} />
              ) : (
                <div className="placeholder-image">
                  <p>{scene.image_description || "Image is being created..."}</p>
                </div>
              )}
            </div>
            <div className="scene-narration">
              <p className="narration-text">{scene.text}</p>
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
          {(storyData?.scenes || []).map((_, index) => (
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
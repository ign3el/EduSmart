import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiPlay, FiPause, FiSkipForward, FiSkipBack, FiRotateCw } from 'react-icons/fi';
import './StoryPlayer.css';
import Quiz from './Quiz';

const API_DOMAIN = "https://edusmart.ign3el.com";

function StoryPlayer({ storyData, avatar, onRestart, onSave, isSaved = false, isOffline = false, savedStoryId = null, currentJobId = null }) {
  const [currentScene, setCurrentScene] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showQuiz, setShowQuiz] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadMessage, setDownloadMessage] = useState('');
  const [showActionMenu, setShowActionMenu] = useState(false);
  const audioRef = useRef(null);

  const scenes = storyData?.scenes || [];
  const scene = scenes[currentScene];

  const fullAudioUrl = scene?.audio_url ? `${API_DOMAIN}${scene.audio_url}` : '';
  const fullImageUrl = scene?.image_url ? `${API_DOMAIN}${scene.image_url}` : '';
  const uploadUrl = storyData?.upload_url ? `${API_DOMAIN}${storyData.upload_url}` : '';

  // Handle Play/Pause Toggle
  useEffect(() => {
    if (audioRef.current) {
      if (isPlaying) {
        const playPromise = audioRef.current.play();
        if (playPromise !== undefined) {
          playPromise.catch(err => {
            console.error("Audio play failed:", err);
            setIsPlaying(false);
          });
        }
      } else {
        audioRef.current.pause();
      }
    }
  }, [isPlaying]);

  // Handle Scene Change and Source Loading
  useEffect(() => {
    setProgress(0);
    if (audioRef.current) {
      audioRef.current.src = fullAudioUrl;
      audioRef.current.load(); // Force the browser to load the new scene's audio
      
      if (isPlaying) {
        const playPromise = audioRef.current.play();
        if (playPromise !== undefined) {
          playPromise.catch(err => console.error("Audio interrupted on scene change:", err));
        }
      }
    }
  }, [currentScene, fullAudioUrl]);

  const goToNextScene = () => {
    if (currentScene < scenes.length - 1) {
      setCurrentScene(currentScene + 1);
    } else {
      setIsPlaying(false);
      setShowQuiz(true);
    }
  };

  const goToPrevScene = () => {
    if (currentScene > 0) {
      setCurrentScene(currentScene - 1);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current && audioRef.current.duration) {
      const newProgress = (audioRef.current.currentTime / audioRef.current.duration) * 100;
      setProgress(newProgress);
    }
  };
  
  const handleAudioEnded = () => {
    // Optional: Auto-advance to next scene when audio ends
    if (currentScene < scenes.length - 1) {
        goToNextScene();
    } else {
        setIsPlaying(false);
    }
  };

  const handleDotClick = (index) => {
    setCurrentScene(index);
  };

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const handleOfflineDownload = async () => {
    // Determine which ID to use for export
    const exportId = savedStoryId || currentJobId;
    const isJobExport = !savedStoryId && currentJobId;

    if (!exportId) {
      // Fallback: local save for truly offline generated stories
      const storyName = prompt('Enter story name for offline save:', storyData.title || 'My Story');
      if (storyName?.trim()) {
        const storyId = `local_${Date.now()}`;
        const localStory = {
          id: storyId,
          name: storyName.trim(),
          storyData: storyData,
          savedAt: Date.now(),
          isOffline: true
        };
        try {
          localStorage.setItem(`edusmart_story_${storyId}`, JSON.stringify(localStory));
          alert(`✅ Story "${storyName}" saved locally for offline viewing!\n\nYou can access it anytime from the Offline Manager, even without internet.`);
        } catch (error) {
          alert('Failed to save locally: ' + error.message);
        }
      }
      return;
    }

    setIsDownloading(true);
    setDownloadMessage('Zipping file...');

    try {
      const endpoint = isJobExport ? `/api/export-job/${exportId}` : `/api/export-story/${exportId}`;
      const response = await fetch(endpoint);
      if (!response.ok) throw new Error('Failed to download story');

      setDownloadMessage('Downloading...');
      const blob = await response.blob();

      setDownloadMessage('Saving file...');
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      const safeName = (storyData.title || 'My Story').replace(/\s+/g, '_');
      link.href = url;
      link.download = `${safeName}_${exportId.substring(0, 8)}.zip`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setDownloadMessage('Complete! ✓');
      setTimeout(() => {
        setDownloadMessage('');
        setIsDownloading(false);
      }, 2000);
    } catch (error) {
      setDownloadMessage(`Error: ${error.message}`);
      setTimeout(() => {
        setDownloadMessage('');
        setIsDownloading(false);
      }, 3000);
    }
  };

  if (showQuiz && storyData?.quiz) {
    return (
      <div className="story-player">
        <Quiz questions={storyData.quiz} onComplete={onRestart} />
      </div>
    );
  }

  if (!scene) {
    return (
      <div className="story-player">
        <p>Story is loading...</p>
        <button className="restart-btn" onClick={onRestart}>
          <FiRotateCw /> Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="story-player">
      <audio
        ref={audioRef}
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleAudioEnded}
        preload="auto"
        crossOrigin="anonymous" // Add this line!
      />
      
      <div className="player-header">
        <h2>🎬 {storyData.title || "Story Time"}</h2>
        <button className="restart-btn" onClick={onRestart}>
          <FiRotateCw /> New Story
        </button>
        {uploadUrl && (
          <a className="upload-link" href={uploadUrl} target="_blank" rel="noreferrer">
            See Your Uploaded File
          </a>
        )}
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
                  <p>{scene.image_description || "Creating your illustration..."}</p>
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
          <button 
            onClick={goToPrevScene} 
            disabled={currentScene === 0} 
            className="control-btn"
          >
            <FiSkipBack />
          </button>
          
          <button onClick={togglePlay} className="control-btn play-btn">
            {isPlaying ? <FiPause /> : <FiPlay />}
          </button>
          
          <button onClick={goToNextScene} className="control-btn next-btn">
            {currentScene === scenes.length - 1 ? "📝 Quiz" : <FiSkipForward />}
          </button>
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

      <div className="action-buttons-overlay">
        <motion.button 
          className="action-menu-toggle"
          onClick={() => setShowActionMenu(!showActionMenu)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          ⚙️
        </motion.button>
        
        <AnimatePresence>
          {showActionMenu && (
            <motion.div 
              className="action-menu"
              initial={{ opacity: 0, scale: 0.8, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: 20 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              onClick={(e) => e.stopPropagation()}
            >
              {!isSaved && !isOffline && onSave && (
                <button className="action-menu-item save-online" onClick={() => { onSave(); setShowActionMenu(false); }}>
                  <span className="action-icon">💾</span>
                  <span>Save Online</span>
                </button>
              )}
              {!isOffline && (
                <button 
                  className="action-menu-item download-offline" 
                  onClick={() => { handleOfflineDownload(); setShowActionMenu(false); }}
                  disabled={isDownloading}
                >
                  <span className="action-icon">📥</span>
                  <span>{isDownloading ? 'Downloading...' : 'Download Offline'}</span>
                </button>
              )}
              <button className="action-menu-item go-home" onClick={() => { onRestart(); setShowActionMenu(false); }}>
                <span className="action-icon"><FiRotateCw /></span>
                <span>{isSaved || isOffline ? 'Back Home' : 'New Story'}</span>
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {downloadMessage && (
        <motion.div 
          className="download-popup"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
        >
          <div className="download-popup-content">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {downloadMessage !== 'Complete! ✓' && !downloadMessage.startsWith('Error') ? <div className="spinner"></div> : <span style={{ fontSize: '1.2rem' }}>✓</span>}
              <p style={{ margin: 0 }}>{downloadMessage}</p>
            </div>
            
            <div className="progress-bar-container">
              <div 
                className="progress-bar"
                style={{
                  width: downloadMessage === 'Zipping file...' ? '25%' : 
                         downloadMessage === 'Downloading...' ? '60%' : 
                         downloadMessage === 'Saving file...' ? '85%' : '100%',
                  transition: 'width 0.4s ease'
                }}
              ></div>
            </div>
            
            <div className="progress-steps">
              <div className={`progress-step ${downloadMessage === 'Zipping file...' ? 'active' : downloadMessage === 'Downloading...' || downloadMessage === 'Saving file...' || downloadMessage === 'Complete! ✓' ? 'completed' : ''}`}>
                <div className="step-dot">1</div>
                <span>Zip</span>
              </div>
              <div className={`progress-step ${downloadMessage === 'Downloading...' ? 'active' : downloadMessage === 'Saving file...' || downloadMessage === 'Complete! ✓' ? 'completed' : ''}`}>
                <div className="step-dot">2</div>
                <span>Download</span>
              </div>
              <div className={`progress-step ${downloadMessage === 'Saving file...' ? 'active' : downloadMessage === 'Complete! ✓' ? 'completed' : ''}`}>
                <div className="step-dot">3</div>
                <span>Save</span>
              </div>
              <div className={`progress-step ${downloadMessage === 'Complete! ✓' ? 'completed' : ''}`}>
                <div className="step-dot">✓</div>
                <span>Done</span>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default StoryPlayer;
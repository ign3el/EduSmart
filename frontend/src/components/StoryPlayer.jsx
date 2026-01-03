import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiPlay, FiPause, FiSkipForward, FiSkipBack, FiRotateCw } from 'react-icons/fi';
import './StoryPlayer.css';
import Quiz from './Quiz';

const API_DOMAIN = "https://edusmart.ign3el.com";

function StoryPlayer({ storyData, avatar, onRestart, onSave, isSaved = false, isOffline = false, savedStoryId = null, currentJobId = null, totalScenes = 0, completedSceneCount = 0 }) {
  const [currentScene, setCurrentScene] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showQuiz, setShowQuiz] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadMessage, setDownloadMessage] = useState('');
  const [showActionMenu, setShowActionMenu] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [generatingMessage, setGeneratingMessage] = useState('');
  const audioRef = useRef(null);
  const imageCache = useRef({});

  const scenes = storyData?.scenes || [];
  const actualTotalScenes = totalScenes > 0 ? totalScenes : scenes.length;
  const scene = scenes[currentScene];

  const fullAudioUrl = scene?.audio_url ? `${API_DOMAIN}${scene.audio_url}` : '';
  const fullImageUrl = scene?.image_url ? `${API_DOMAIN}${scene.image_url}` : '';
  const uploadUrl = storyData?.upload_url ? `${API_DOMAIN}${storyData.upload_url}` : '';

  // Preload all scene images when story loads
  useEffect(() => {
    scenes.forEach((scene, index) => {
      const imageUrl = scene?.image_url ? `${API_DOMAIN}${scene.image_url}` : '';
      if (imageUrl && !imageCache.current[imageUrl]) {
        const img = new Image();
        img.onload = () => {
          imageCache.current[imageUrl] = true;
        };
        img.src = imageUrl;
      }
    });
  }, [scenes]);

  // Preload next scene's image and audio in background (for immediate next scene)
  useEffect(() => {
    if (currentScene < scenes.length - 1) {
      const nextScene = scenes[currentScene + 1];
      const nextImageUrl = nextScene?.image_url ? `${API_DOMAIN}${nextScene.image_url}` : '';
      const nextAudioUrl = nextScene?.audio_url ? `${API_DOMAIN}${nextScene.audio_url}` : '';
      
      // Preload next image
      if (nextImageUrl && !imageCache.current[nextImageUrl]) {
        const img = new Image();
        img.onload = () => {
          imageCache.current[nextImageUrl] = true;
        };
        img.src = nextImageUrl;
      }
      
      // Preload next audio
      if (nextAudioUrl && !imageCache.current[nextAudioUrl]) {
        const audio = new Audio();
        audio.onloadeddata = () => {
          imageCache.current[nextAudioUrl] = true;
        };
        audio.src = nextAudioUrl;
      }
    }
  }, [currentScene, scenes]);

  useEffect(() => {
    
    // Test if image endpoint is accessible
    if (fullImageUrl) {
      fetch(fullImageUrl, { method: 'HEAD' })
        .then(res => {
          if (!res.ok) {
          }
        })
        .catch(err => console.error('HEAD request failed:', err));
      
      // Try to load the image directly to see any errors
      const testImg = new Image();
      testImg.src = fullImageUrl;
    }
  }, [currentScene, fullImageUrl, imageLoaded, imageError]);

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
    setImageLoaded(false);
    setImageError(false);
    
    // Pre-load image to ensure onLoad fires
    if (fullImageUrl) {
      const img = new Image();
      img.onload = () => {
        setImageLoaded(true);
      };
      img.onerror = () => {
        setImageError(true);
      };
      img.src = fullImageUrl;
    }
    
    if (audioRef.current) {
      // Stop current audio immediately to prevent overlap
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      
      // Update to new scene's audio
      audioRef.current.src = fullAudioUrl;
      audioRef.current.load(); // Force the browser to load the new scene's audio
      
      // Only auto-play if isPlaying state is true
      if (isPlaying) {
        const playPromise = audioRef.current.play();
        if (playPromise !== undefined) {
          playPromise.catch(err => {
            console.error("Audio interrupted on scene change:", err);
            setIsPlaying(false);
          });
        }
      }
    }
  }, [currentScene, fullAudioUrl, fullImageUrl, isPlaying]);

  const goToNextScene = () => {
    if (currentScene < scenes.length - 1) {
      // Stop current audio before changing scene
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      setCurrentScene(currentScene + 1);
      setGeneratingMessage('');
    } else if (currentScene < actualTotalScenes - 1) {
      // Trying to go to a scene that hasn't been generated yet
      setGeneratingMessage(`Scene ${currentScene + 2} is still being generated. Please wait...`);
      setTimeout(() => setGeneratingMessage(''), 3000);
    } else {
      setIsPlaying(false);
      setShowQuiz(true);
    }
  };

  const goToPrevScene = () => {
    if (currentScene > 0) {
      // Stop current audio before changing scene
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      setCurrentScene(currentScene - 1);
      setGeneratingMessage('');
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current && audioRef.current.duration) {
      const newProgress = (audioRef.current.currentTime / audioRef.current.duration) * 100;
      setProgress(newProgress);
    }
  };
  
  const handleAudioEnded = () => {
    // Only auto-advance if we're still on the same scene that finished playing
    // This prevents issues when user manually changes scenes while audio is playing
    if (audioRef.current && audioRef.current.currentTime > 0) {
      if (currentScene < scenes.length - 1) {
        goToNextScene();
      } else {
        setIsPlaying(false);
        setShowQuiz(true);
      }
    }
  };

  const handleDotClick = (index) => {
    // Check if scene is available
    if (index >= scenes.length) {
      setGeneratingMessage(`Scene ${index + 1} is still being generated. Please wait...`);
      setTimeout(() => setGeneratingMessage(''), 3000);
      return;
    }
    
    // Stop current audio before changing scene
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setCurrentScene(index);
    setGeneratingMessage('');
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
          // Trigger storage event for OfflineManager to refresh
          window.dispatchEvent(new StorageEvent('storage', {
            key: `edusmart_story_${storyId}`,
            newValue: JSON.stringify(localStory),
            storageArea: localStorage
          }));
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
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
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
              {fullImageUrl && !imageError && imageLoaded ? (
                <>
                  <img 
                    src={fullImageUrl} 
                    alt={`Scene ${currentScene + 1}`}
                  />
                </>
              ) : (
                <>
                  <div className="placeholder-image">
                    <p>{imageError ? 'Image unavailable - check console' : (scene?.image_description || "Loading image...")}</p>
                  </div>
                </>
              )}
            </div>
            <div className="scene-right">
              <div className="scene-narration">
                <p className="narration-text">{scene.text}</p>
              </div>

              <div className="player-controls inline-controls">
                <div className="scene-counter">
                  Scene {currentScene + 1} of {actualTotalScenes}
                  {currentJobId && completedSceneCount < actualTotalScenes && (
                    <span className="generating-indicator"> • {completedSceneCount} scenes ready</span>
                  )}
                </div>
                
                {generatingMessage && (
                  <div className="generating-message">{generatingMessage}</div>
                )}
                
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
                  {Array.from({ length: actualTotalScenes }, (_, index) => {
                    const isAvailable = index < scenes.length;
                    const isActive = index === currentScene;
                    const isCompleted = index < currentScene;
                    
                    return (
                      <button
                        key={`dot-${index}`}
                        className={`dot ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''} ${!isAvailable ? 'unavailable' : ''}`}
                        onClick={() => handleDotClick(index)}
                        title={!isAvailable ? `Scene ${index + 1} is still generating` : `Go to scene ${index + 1}`}
                      />
                    );
                  })}
                </div>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      <div className="action-buttons-overlay">
        <motion.button 
          className="action-menu-toggle"
          onClick={() => setShowActionMenu(!showActionMenu)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          ⋮
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
import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiPlay, FiPause, FiSkipForward, FiSkipBack, FiRotateCw } from 'react-icons/fi';
import './StoryPlayer.css';
import Quiz from './Quiz';

// Helper function to build full URL, handling absolute URLs, data URLs, and API paths
const buildFullUrl = (url) => {
  if (!url) {
    return '';
  }
  
  // Check if already absolute (http/https) or data URL
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url;
  }
  
  // Check if it's an API path (starts with /api/)
  if (url.startsWith('/api/')) {
    // Use the current window's origin to build the full URL
    return `${window.location.origin}${url}`;
  }
  
  // For other relative paths, prepend the API domain from environment or current origin
  const apiDomain = import.meta.env.VITE_API_URL || window.location.origin;
  return `${apiDomain}${url}`;
};

const StoryPlayer = forwardRef(({ storyData, avatar, onRestart, onSave, onDownloadOffline, isSaved = false, isOffline = false, savedStoryId = null, currentJobId = null, totalScenes = 0, completedSceneCount = 0 }, ref) => {
  const [currentScene, setCurrentScene] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showQuiz, setShowQuiz] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadMessage, setDownloadMessage] = useState('');
  const [showActionMenu, setShowActionMenu] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [generatingMessage, setGeneratingMessage] = useState('');
  const [savedTime, setSavedTime] = useState(0); // Track saved playback position
  const audioRef = useRef(null);
  const imageCache = useRef({});

  const scenes = storyData?.scenes || [];
  const actualTotalScenes = totalScenes > 0 ? totalScenes : scenes.length;
  const scene = scenes[currentScene];

  const fullAudioUrl = buildFullUrl(scene?.audio_url);
  const fullImageUrl = buildFullUrl(scene?.image_url);
  const uploadUrl = buildFullUrl(storyData?.upload_url);
  
  // Debug logging for URL construction
  useEffect(() => {
    if (scene?.audio_url) {
      console.log('🎵 Audio URL Debug:', {
        original: scene.audio_url,
        built: fullAudioUrl,
        isAbsolute: fullAudioUrl.startsWith('http')
      });
    }
    if (scene?.image_url) {
      console.log('🖼️ Image URL Debug:', {
        original: scene.image_url,
        built: fullImageUrl,
        isAbsolute: fullImageUrl.startsWith('http')
      });
    }
  }, [scene, fullAudioUrl, fullImageUrl]);
  
  // Audio error state
  const [audioError, setAudioError] = useState(false);
  const [audioRetryCount, setAudioRetryCount] = useState(0);

  // Expose download function to parent component
  useImperativeHandle(ref, () => ({
    triggerDownload: () => handleOfflineDownload()
  }));

  // Preload all scene images when story loads
  useEffect(() => {
    scenes.forEach((scene, index) => {
      const imageUrl = buildFullUrl(scene?.image_url);
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
      const nextImageUrl = buildFullUrl(nextScene?.image_url);
      const nextAudioUrl = buildFullUrl(nextScene?.audio_url);
      
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
    // Pre-test image accessibility (silent)
    if (fullImageUrl) {
      const testImg = new Image();
      testImg.onload = () => {
        console.log('✅ Image pre-test successful:', fullImageUrl);
      };
      testImg.onerror = () => {
        console.warn('⚠️ Image pre-test failed:', fullImageUrl);
      };
      testImg.src = fullImageUrl;
    }
  }, [currentScene, fullImageUrl, imageLoaded, imageError]);

  // Handle Play/Pause Toggle - Robust state management
  const [userPaused, setUserPaused] = useState(false);
  const [systemPaused, setSystemPaused] = useState(false);
  
  // Save current time when user pauses
  const handlePause = () => {
    if (audioRef.current) {
      setSavedTime(audioRef.current.currentTime);
      console.log('⏸️ User paused at:', audioRef.current.currentTime);
    }
  };
  
  // Resume from saved time when user plays
  const handlePlay = () => {
    if (audioRef.current && savedTime > 0) {
      audioRef.current.currentTime = savedTime;
      console.log('▶️ Audio resumed from:', savedTime);
    }
  };
  
  useEffect(() => {
    if (audioRef.current) {
      const handlePlay = () => {
        console.log('▶️ Audio started playing');
        setSystemPaused(false);
        setIsPlaying(true);
      };
      
      const handlePause = () => {
        console.log('⏸️ Audio paused');
        // Only set system paused if not user-initiated
        if (!userPaused) {
          setSystemPaused(true);
        }
      };
      
      const handleEnded = () => {
        console.log('⏹️ Audio ended');
        setSystemPaused(false);
        setUserPaused(false);
      };
      
      audioRef.current.addEventListener('play', handlePlay);
      audioRef.current.addEventListener('pause', handlePause);
      audioRef.current.addEventListener('ended', handleEnded);
      
      return () => {
        if (audioRef.current) {
          audioRef.current.removeEventListener('play', handlePlay);
          audioRef.current.removeEventListener('pause', handlePause);
          audioRef.current.removeEventListener('ended', handleEnded);
        }
      };
    }
  }, [userPaused]);

  // Combined play/pause logic
  useEffect(() => {
    if (audioRef.current) {
      const shouldPlay = isPlaying && !userPaused && !systemPaused;
      const isCurrentlyPlaying = !audioRef.current.paused;
      
      if (shouldPlay && !isCurrentlyPlaying) {
        const playPromise = audioRef.current.play();
        if (playPromise !== undefined) {
          playPromise.catch(err => {
            console.error("Audio play failed:", err);
            setIsPlaying(false);
            setUserPaused(true);
          });
        }
      } else if (!shouldPlay && isCurrentlyPlaying) {
        audioRef.current.pause();
      }
    }
  }, [isPlaying, userPaused, systemPaused]);

  // Handle Scene Change and Source Loading
  useEffect(() => {
    // Reset progress and time for new scene
    setProgress(0);
    setCurrentTime(0);
    setDuration(0);
    setSavedTime(0); // Reset saved time when scene changes
    setImageLoaded(false);
    setImageError(false);
    setAudioError(false);
    
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
      
      // Update to new scene's audio with cache-busting for fresh load
      const audioUrlWithCacheBust = fullAudioUrl ? 
        `${fullAudioUrl}${fullAudioUrl.includes('?') ? '&' : '?'}v=${audioRetryCount}` : '';
      
      audioRef.current.src = audioUrlWithCacheBust;
      audioRef.current.load(); // Force the browser to load the new scene's audio
      
      // Add error handler for audio
      const handleAudioError = (e) => {
        console.error('Audio loading error:', e.target.error);
        setAudioError(true);
      };
      
      audioRef.current.addEventListener('error', handleAudioError);
      
      // If isPlaying is true, wait for audio to be ready before playing
      if (isPlaying) {
        const handleCanPlay = () => {
          if (audioRef.current && isPlaying && !audioError) {
            const playPromise = audioRef.current.play();
            if (playPromise !== undefined) {
              playPromise.catch(err => {
                console.error('Scene change auto-play failed:', err);
                setIsPlaying(false);
                setAudioError(true);
              });
            }
          }
          audioRef.current?.removeEventListener('canplay', handleCanPlay);
        };
        audioRef.current.addEventListener('canplay', handleCanPlay);
      }
      
      return () => {
        if (audioRef.current) {
          audioRef.current.removeEventListener('error', handleAudioError);
        }
      };
    }
  }, [currentScene, fullAudioUrl, fullImageUrl, isPlaying, audioRetryCount]);

  const handleQuizClick = () => {
    console.log('🎯 Quiz button clicked - starting quiz...')
    setIsPlaying(false)
    setShowQuiz(true)
  };

  const goToNextScene = () => {
    if (currentScene < scenes.length - 1) {
      // Stop current audio before changing scene
      if (audioRef.current) {
        audioRef.current.pause();
        // Don't reset currentTime here - it will be reset in the scene change useEffect
      }
      setCurrentScene(currentScene + 1);
      setGeneratingMessage('');
      // Auto-play next scene
      setIsPlaying(true);
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
        // Don't reset currentTime here - it will be reset in the scene change useEffect
      }
      setCurrentScene(currentScene - 1);
      setGeneratingMessage('');
      // Auto-play previous scene
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current && audioRef.current.duration) {
      const newProgress = (audioRef.current.currentTime / audioRef.current.duration) * 100;
      setProgress(newProgress);
      setCurrentTime(audioRef.current.currentTime);
      setDuration(audioRef.current.duration);
    }
  };
  
  const handleSeek = (e) => {
    if (audioRef.current && audioRef.current.duration) {
      const rect = e.currentTarget.getBoundingClientRect();
      // Handle both click and touch events
      const clientX = e.type && e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
      const x = clientX - rect.left;
      const percentage = x / rect.width;
      const newTime = percentage * audioRef.current.duration;
      audioRef.current.currentTime = newTime;
      setCurrentTime(newTime);
      setProgress(percentage * 100);
    }
  };
  
  const formatTime = (time) => {
    if (isNaN(time)) return '0:00';
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
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
      // Don't reset currentTime here - it will be reset in the scene change useEffect
    }
    setCurrentScene(index);
    setGeneratingMessage('');
    // Auto-play selected scene
    setIsPlaying(true);
  };

  const togglePlay = () => {
    if (audioRef.current) {
      const isCurrentlyPlaying = !audioRef.current.paused;
      
      if (isCurrentlyPlaying) {
        // Capture current time BEFORE pausing
        const currentPosition = audioRef.current.currentTime;
        audioRef.current.pause();
        setSavedTime(currentPosition); // Update saved time immediately
        setIsPlaying(false);
        console.log('⏸️ User paused at:', currentPosition);
      } else {
        // Use ref to bypass state closure issues
        const targetTime = savedTime > 0 ? savedTime : 0;
        audioRef.current.currentTime = targetTime;
        
        // If audio error occurred, retry loading
        if (audioError) {
          setAudioRetryCount(prev => prev + 1);
          setAudioError(false);
          return;
        }
        
        audioRef.current.play()
          .then(() => {
            setIsPlaying(true);
            console.log('▶️ Audio resumed from:', targetTime);
          })
          .catch(err => {
            console.error('Play error:', err);
            setAudioError(true);
          });
      }
    }
  };
  
  const retryAudio = () => {
    setAudioRetryCount(prev => prev + 1);
    setAudioError(false);
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
    console.log('✅ Rendering Quiz - questions:', storyData.quiz.length)
    return (
      <div className="story-player">
        <Quiz questions={storyData.quiz} onComplete={onRestart} />
      </div>
    );
  }

  if (showQuiz && !storyData?.quiz) {
    console.log('⚠️ Quiz mode but no quiz data available')
    console.log('📊 storyData structure:', {
      hasStoryData: !!storyData,
      storyDataKeys: storyData ? Object.keys(storyData) : [],
      hasQuiz: !!storyData?.quiz,
      scenes: storyData?.scenes?.length
    })
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
        crossOrigin="anonymous"
        onError={(e) => {
          console.error('Audio element error:', e.target.error);
          setAudioError(true);
        }}
      />
      
      <div className="player-header">
        <h2>🎬 {storyData.title || "Story Time"}</h2>
      </div>
      
      {/* Audio Error Notification */}
      {audioError && (
        <div className="audio-error-banner">
          <p>🔊 Audio unavailable - {scene?.audio_url ? 'loading failed' : 'no audio file'}</p>
          <button onClick={retryAudio} className="retry-btn">
            Retry Audio
          </button>
        </div>
      )}

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
              {fullImageUrl && !imageError ? (
                <img 
                  src={fullImageUrl} 
                  alt={`Scene ${currentScene + 1}`}
                  onLoad={(e) => {
                    if (!imageLoaded) setImageLoaded(true);
                    if (imageError) setImageError(false);
                  }}
                  onError={(e) => {
                    if (!imageError) setImageError(true);
                    if (imageLoaded) setImageLoaded(false);
                  }}
                  crossOrigin="anonymous"
                />
              ) : (
                <div className="placeholder-image">
                  <p>{imageError ? 'Image unavailable' : (scene?.image_description || "Loading image...")}</p>
                </div>
              )}
            </div>
            <div className="scene-right">
              <div className="scene-narration">
                <p className="narration-text">{scene.text}</p>
              </div>

              <div className="player-controls inline-controls">
                {/* Audio Progress Bar */}
                <div className="audio-progress-section">
                  <span className="time-display">{formatTime(currentTime)}</span>
                  <div className="audio-progress-bar" onClick={handleSeek} onTouchStart={handleSeek}>
                    <div className="audio-progress-fill" style={{ width: `${progress}%` }} />
                    <div className="audio-progress-handle" style={{ left: `${progress}%` }} />
                  </div>
                  <span className="time-display">{formatTime(duration)}</span>
                </div>

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
                  
                  <button onClick={currentScene === scenes.length - 1 ? handleQuizClick : goToNextScene} className="control-btn next-btn" title={currentScene === scenes.length - 1 ? 'Take Quiz' : 'Next Scene'}>
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

      <div className="action-buttons-overlay">
        {/* Action menu removed - now using global FloatingMenu */}
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
});

StoryPlayer.displayName = 'StoryPlayer';

export default StoryPlayer;

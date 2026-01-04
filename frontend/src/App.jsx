import { useState, useEffect, useRef, lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from './context/AuthContext'
import apiClient from './services/api'
import Login from './components/Login'
import Signup from './components/Signup'
import VerifyEmail from './components/VerifyEmail'
import ForgotPassword from './components/ForgotPassword'
import ResetPassword from './components/ResetPassword'
import FileUpload from './components/FileUpload'
import FileConfirmation from './components/FileConfirmation'
import AvatarSelector from './components/AvatarSelector'
import StoryPlayer from './components/StoryPlayer'
import SaveStoryModal from './components/SaveStoryModal'
import LoadStory from './components/LoadStory'
import OfflineManager from './components/OfflineManager'
import UserProfile from './components/UserProfile'
import ReuploadConfirmModal from './components/ReuploadConfirmModal'
import UploadProgressOverlay from './components/UploadProgressOverlay'
import TeacherCard from './components/TeacherCard'
import NavigationMenu from './components/NavigationMenu'
import StoryActionsBar from './components/StoryActionsBar'
const AdminPanel = lazy(() => import('./components/AdminPanel'));
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  // Use Routes to handle verification and password reset pages
  return (
    <Routes>
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/*" element={<MainApp />} />
    </Routes>
  )
}

function MainApp() {
  const { user, isAuthenticated, isLoading, logout } = useAuth()
  const [authStep, setAuthStep] = useState('login') // 'login' or 'signup'
  const [signupSuccess, setSignupSuccess] = useState(false)
  const [step, setStep] = useState('home') 
  const [uploadedFile, setUploadedFile] = useState(null)
  const [selectedAvatar, setSelectedAvatar] = useState(null)
  // New state for Kokoro TTS
  const [voice, setVoice] = useState('af_sarah');
  const [speed, setSpeed] = useState(1.0);
  const [detectedLanguage, setDetectedLanguage] = useState('en');
  
  const [storyData, setStoryData] = useState(null)
  const storyPlayerRef = useRef(null);
  const [progress, setProgress] = useState(0)
  const [totalScenes, setTotalScenes] = useState(0) // Track total scenes from backend
  const [completedSceneCount, setCompletedSceneCount] = useState(0) // Track completed scenes
  const [error, setError] = useState(null)
  const [gradeLevel, setGradeLevel] = useState(3)
  const [currentJobId, setCurrentJobId] = useState(null)
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [isSaved, setIsSaved] = useState(false)
  const [savedStoryId, setSavedStoryId] = useState(null)
  const [isOfflineMode, setIsOfflineMode] = useState(false)
  const [showReuploadModal, setShowReuploadModal] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadFileName, setUploadFileName] = useState('')
  const [showUploadProgress, setShowUploadProgress] = useState(false)
  const fileInputRef = useRef(null)

  // Handle browser back button to navigate within app steps
  useEffect(() => {
    const handlePopState = (event) => {
      if (event.state && event.state.step) {
        // Use the step from history state
        setStep(event.state.step)
      } else {
        // Fallback to previous step logic
        const prev = previousStep(step)
        setStep(prev)
      }
    }

    // Push current step to history
    window.history.replaceState({ step }, '', window.location.pathname)
    window.addEventListener('popstate', handlePopState)
    
    return () => window.removeEventListener('popstate', handlePopState)
  }, [step])

  const navigateTo = (newStep) => {
    window.history.pushState({ step: newStep }, '', window.location.pathname)
    setStep(newStep)
  }

  // If not logged in and not loading, show auth screen
  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <div style={{ color: 'white', fontSize: '20px' }}>Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    if (signupSuccess) {
      return (
        <div className="auth-container" style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          color: 'white'
        }}>
          <motion.div 
            className="auth-box" 
            initial={{ opacity: 0, y: 20 }} 
            animate={{ opacity: 1, y: 0 }}
          >
            <h2>Signup Successful!</h2>
            <p style={{ margin: '20px 0' }}>Please check your email to verify your account, then you can log in.</p>
            <button className="auth-button" onClick={() => {
              setSignupSuccess(false);
              setAuthStep('login');
            }}>
              Proceed to Login
            </button>
          </motion.div>
        </div>
      );
    }

    return (
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <AnimatePresence mode="wait">
          {authStep === 'login' ? (
            <Login
              key="login"
              onSwitchToSignup={() => setAuthStep('signup')}
            />
          ) : (
            <Signup
              key="signup"
              onSwitchToLogin={() => setAuthStep('login')}
              onSuccess={() => setSignupSuccess(true)}
            />
          )}
        </AnimatePresence>
      </div>
    )
  }

  const previousStep = (current) => {
    switch (current) {
      case 'playing':
      case 'generating':
        return 'confirm'
      case 'confirm':
        return 'upload'
      case 'upload':
      case 'offline':
      case 'load':
      case 'profile':
      default:
        return 'home'
    }
  }

  const handleFileUpload = (file) => {
    setUploadedFile(file)
    setUploadFileName(file.name)
    setShowUploadProgress(true)
    setUploadProgress(0)
    
    // Simulate upload progress
    let progress = 0
    const interval = setInterval(() => {
      progress += Math.random() * 30
      if (progress >= 90) progress = 90
      setUploadProgress(Math.round(progress))
    }, 300)
    
    // Complete upload
    setTimeout(() => {
      clearInterval(interval)
      setUploadProgress(100)
      
      // Proceed after completion
      setTimeout(() => {
        setShowUploadProgress(false)
        navigateTo('confirm')
        setError(null) 
        setIsSaved(false)
      }, 800)
    }, 2000)
  }

  const handleReuploadClick = () => {
    setShowReuploadModal(true)
  }

  const handleReuploadConfirm = () => {
    setShowReuploadModal(false)
    // Trigger hidden file input instead of navigating
    if (fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  const handleFileInputChange = (e) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleConfirmFile = (settings) => {
    if (settings) {
      setVoice(settings.voice);
      setSpeed(settings.speed);
    }
    navigateTo('avatar')
  }

  const handleAvatarSelect = async (avatar) => {
    setSelectedAvatar(avatar)
    await generateStory(avatar)
  }

  const generateStory = async (avatar) => {
    try {
      navigateTo('generating')
      setError(null)
      setProgress(0)
      setIsSaved(false)

      const formData = new FormData()
      formData.append('file', uploadedFile)
      formData.append('grade_level', gradeLevel)
      formData.append('avatar_type', avatar.id)
      // Append new Kokoro TTS settings
      formData.append('voice', voice)
      formData.append('speed', speed)

      // Use apiClient for automatic auth headers, assuming it's the default export from api.js
      const response = await fetch(`${API_URL}/api/upload`, { 
        method: 'POST', 
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      })
      
      if (!response.ok) throw new Error("Failed to start story generation.")
      
      const { job_id } = await response.json()
      setCurrentJobId(job_id)

      // Polling Loop
      const pollTimer = setInterval(async () => {
        try {
          const statusRes = await fetch(`/api/status/${job_id}`)
          if (!statusRes.ok) throw new Error("Could not fetch status")
          
          const job = await statusRes.json()

          if (job.status === 'processing') {
            setProgress((prev) => Math.max(prev, job.progress ?? prev))
            
            // Update total scenes count when available
            if (job.total_scenes > 0) {
              setTotalScenes(job.total_scenes)
              setCompletedSceneCount(job.completed_scene_count || 0)
            }
            
            // Show story immediately when first scene is ready
            if (job.result && job.result.scenes && job.result.scenes.length > 0) {
              if (!storyData || storyData.scenes.length === 0) {
                // First scene is ready - show it immediately
                setStoryData(job.result)
                navigateTo('playing')
              } else {
                // Update story data with newly completed scenes
                setStoryData(job.result)
              }
            }
          } else if (job.status === 'completed') {
            clearInterval(pollTimer)
            setStoryData(job.result)
            setProgress(100)
            if (job.total_scenes > 0) {
              setTotalScenes(job.total_scenes)
              setCompletedSceneCount(job.total_scenes)
            }
            navigateTo('playing')
          } else if (job.status === 'failed') {
            clearInterval(pollTimer)
            throw new Error(job.error || "AI Generation failed.")
          }
        } catch (err) {
          clearInterval(pollTimer)
          setError("Connection lost: " + err.message)
          navigateTo('upload')
        }
      }, 2000)

    } catch (err) {
      setError(err.message)
      navigateTo('upload')
    }
  }

  const handleRestart = async () => {
    // Cleanup unsaved story
    if (currentJobId && !isSaved) {
      try {
        await fetch(`/api/cleanup/${currentJobId}`, { method: 'DELETE' })
      } catch (error) {
        console.error('Cleanup failed:', error)
      }
    }
    
    navigateTo('home')
    setUploadedFile(null)
    setSelectedAvatar(null)
    setStoryData(null)
    setError(null)
    setProgress(0)
    setTotalScenes(0)
    setCompletedSceneCount(0)
    setCurrentJobId(null)
    setIsSaved(false)
    setSavedStoryId(null)
    setIsOfflineMode(false)
  }

  const handleSaveStory = () => {
    setShowSaveModal(true)
  }

  const handleSaveComplete = async (storyId, storyName) => {
    setShowSaveModal(false)
    setIsSaved(true)
    setSavedStoryId(storyId)
    alert(`✅ Story "${storyName}" saved successfully!`)
  }

  const handleLoadOffline = (loadedStoryData, storyName) => {
    setStoryData(loadedStoryData)
    setSelectedAvatar({ id: 'offline', name: 'Offline Story' })
    setIsSaved(true)
    setIsOfflineMode(true)
    navigateTo('playing')
  }

  const handleSaveOffline = async (storyData, storyName) => {
    try {
      // Save to localStorage
      const storyId = `local_${Date.now()}`
      const localStory = {
        id: storyId,
        name: storyName,
        storyData: storyData,
        savedAt: Date.now(),
        isOffline: true
      }
      
      localStorage.setItem(`edusmart_story_${storyId}`, JSON.stringify(localStory))
      alert(`✅ Story "${storyName}" saved locally!`)
      return storyId
    } catch (error) {
      throw new Error('Failed to save locally: ' + error.message)
    }
  }

  const handlePlayStoryFromAdmin = async (storyId) => {
    if (!storyId) {
      setError('Cannot play story: Invalid story ID');
      return;
    }
    
    try {
      const response = await apiClient.get(`/api/load-story/${storyId}`);
      
      if (response.data && response.data.story_data) {
          setStoryData(response.data.story_data);
          setSelectedAvatar({ id: 'loaded', name: response.data.name });
          setIsSaved(true);
          setSavedStoryId(storyId);
          navigateTo('playing');
      } else {
        setError('Story data is incomplete or invalid');
      }
    } catch (err) {
        console.error('Error loading story:', err);
        setError(`Failed to load story. ${err.response?.data?.detail || err.message}`);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-content">
          <h1>EduSmart</h1>
          <p className="header-subtitle">AI-Powered Storymaker</p>
        </div>
        {isAuthenticated && (
          <NavigationMenu
            user={user}
            isAdmin={user?.is_admin}
            onHome={() => navigateTo('home')}
            onNewStory={step === 'playing' ? () => navigateTo('upload') : null}
            onLoadStories={() => navigateTo('load')}
            onOfflineManager={() => navigateTo('offline')}
            onAdminClick={() => navigateTo('admin')}
            onProfile={() => navigateTo('profile')}
            onLogout={logout}
          />
        )}
      </header>

      <main className="app-main">
        <div className="content-shell">
          {error && (
            <div className="error-message">
              <p>⚠️ {error}</p>
              <button onClick={() => setError(null)}>Try Again</button>
            </div>
          )}
          
          <AnimatePresence mode="wait">
            {step === 'admin' && (
              <Suspense fallback={<div className="loading-message">Loading Admin Panel...</div>}>
                <motion.div key="admin-panel" className="step-container">
                  <AdminPanel 
                    onPlayStory={handlePlayStoryFromAdmin}
                    onBack={() => navigateTo('home')}
                  />
                </motion.div>
              </Suspense>
            )}

            {step === 'home' && (
              <motion.div key="home" className="home-container">
                <div className="home-topline">
                  <h2>Choose how you want to begin</h2>
                  <span className="pill">Smart, fast, and offline-ready</span>
                </div>
                <div className="home-buttons">
                  <motion.button 
                    className="home-btn create-btn"
                    onClick={() => navigateTo('upload')}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <div className="emoji">✨</div>
                    <strong>Create New Story</strong>
                    <span>Upload a lesson file and let AI turn it into a story</span>
                  </motion.button>
                  <motion.button 
                    className="home-btn load-btn"
                    onClick={() => navigateTo('load')}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <div className="emoji">📚</div>
                    <strong>Load Online Story</strong>
                    <span>Pull down a saved adventure from the cloud</span>
                  </motion.button>
                  <motion.button 
                    className="home-btn offline-btn"
                    onClick={() => navigateTo('offline')}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <div className="emoji">📱</div>
                    <strong>Offline Manager</strong>
                    <span>Manage locally stored stories without an internet connection</span>
                  </motion.button>
                </div>
              </motion.div>
            )}

          {step === 'upload' && (
            <motion.div key="upload" className="step-container">
              <FileUpload 
                onUpload={handleFileUpload}
                gradeLevel={gradeLevel}
                onGradeLevelChange={setGradeLevel}
              />
              <button className="back-to-home-btn" onClick={() => navigateTo('home')}>
                ← Back to Home
              </button>
            </motion.div>
          )}

          {step === 'confirm' && (
            <motion.div key="confirm" className="step-container">
              <FileConfirmation
                file={uploadedFile}
                gradeLevel={gradeLevel}
                onConfirm={handleConfirmFile}
                onBack={() => navigateTo('upload')}
                onReupload={handleReuploadClick}
                onEditGrade={(newGrade) => setGradeLevel(newGrade)}
              />
            </motion.div>
          )}

          {step === 'offline' && (
            <motion.div key="offline" className="step-container">
              <OfflineManager 
                onLoadOffline={handleLoadOffline}
                onBack={() => navigateTo('home')}
              />
            </motion.div>
          )}

          {step === 'load' && (
            <motion.div key="load" className="step-container">
              <LoadStory 
                onLoad={(storyData, storyName, storyId) => {
                  setStoryData(storyData)
                  setSelectedAvatar({ id: 'loaded', name: 'Saved Story' })
                  setIsSaved(true)
                  setSavedStoryId(storyId)
                  navigateTo('playing')
                }}
                onBack={() => navigateTo('home')}
              />
            </motion.div>
          )}

          {step === 'profile' && (
            <motion.div key="profile" className="step-container">
              <UserProfile 
                user={user}
                onBack={() => navigateTo('home')}
                onLogout={logout}
              />
            </motion.div>
          )}

          {step === 'avatar' && (
            <motion.div key="avatar" className="step-container">
              <AvatarSelector onSelect={handleAvatarSelect} />
            </motion.div>
          )}

          {step === 'generating' && (
            <motion.div key="generating" className="generating-container">
              <div className="loading-spinner"></div>
              <h2>Creating Your Story...</h2>
              
              <div className="progress-container">
                <div className="progress-bar-bg">
                  <motion.div 
                    className="progress-bar-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                <p>{progress}% Complete</p>
                {totalScenes > 0 && (
                  <p className="scene-progress">
                    {completedSceneCount} of {totalScenes} scenes ready
                  </p>
                )}
              </div>
              
              <p className="small-text">Generating custom images and voiceovers...</p>
            </motion.div>
          )}

          {step === 'playing' && storyData && (
            <>
              <StoryActionsBar
                onSaveOnline={!isSaved ? handleSaveStory : null}
                onDownloadOffline={storyPlayerRef.current ? () => storyPlayerRef.current.triggerDownload() : null}
                isSaved={isSaved}
                isOffline={isOfflineMode}
              />
              <motion.div key="playing" className="player-container">
                <StoryPlayer
                  ref={storyPlayerRef}
                  storyData={storyData} 
                  avatar={selectedAvatar} 
                  onRestart={handleRestart}
                  onSave={handleSaveStory}
                  isSaved={isSaved}
                  isOffline={isOfflineMode}
                  savedStoryId={savedStoryId}
                  currentJobId={currentJobId}
                  totalScenes={totalScenes}
                  completedSceneCount={completedSceneCount}
                />
              </motion.div>
            </>
          )}
        </AnimatePresence>

          {showSaveModal && (
            <SaveStoryModal 
              jobId={currentJobId}
              onSave={handleSaveComplete}
              onCancel={() => setShowSaveModal(false)}
            />
          )}

          {showReuploadModal && (
            <ReuploadConfirmModal
              onConfirm={handleReuploadConfirm}
              onCancel={() => setShowReuploadModal(false)}
            />
          )}

          {showUploadProgress && (
            <UploadProgressOverlay
              progress={uploadProgress}
              fileName={uploadFileName}
              isVisible={showUploadProgress}
            />
          )}

          {/* Hidden file input for re-upload */}
          <input
            ref={fileInputRef}
            type="file"
            id="file-reupload"
            name="file-reupload"
            accept=".pdf,.docx,.doc"
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
          />
        </div>
      </main>
    </div>
  )
}

export default App

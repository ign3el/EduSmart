import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import updateService from '../services/updateService'
import './NavigationMenu.css'

function NavigationMenu({ user, isAdmin, onHome, onNewStory, onLoadStories, onOfflineManager, onAdminClick, onProfile, onLogout, onSaveStory, onDownloadStory, isPlayingStory, currentStory, onShowFileViewer }) {
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const [isCheckingUpdate, setIsCheckingUpdate] = useState(false)
  const [showInstallPrompt, setShowInstallPrompt] = useState(false)
  const [isPWA, setIsPWA] = useState(false)
  const deferredPromptRef = useRef(null)

  // Handle PWA install prompt
  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      console.log('📱 beforeinstallprompt event fired!', {
        userAgent: navigator.userAgent.substring(0, 100),
        standalone: window.matchMedia('(display-mode: standalone)').matches,
        isIOS: /iPhone|iPad|iPod/.test(navigator.userAgent)
      })
      e.preventDefault()
      deferredPromptRef.current = e
      setShowInstallPrompt(true)
      console.log('💾 PWA install prompt ready - Install App button should appear')
    }

    const handleAppInstalled = () => {
      setShowInstallPrompt(false)
      setIsPWA(true)
      console.log('✅ App installed successfully')
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', handleAppInstalled)

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true) {
      setIsPWA(true)
      console.log('✅ App is already in standalone mode')
    }

    console.log('🔍 PWA listener attached - waiting for beforeinstallprompt event...')
    console.log('🌐 Device info:', {
      standalone: window.matchMedia('(display-mode: standalone)').matches,
      isIOS: /iPhone|iPad|iPod/.test(navigator.userAgent),
      isAndroid: /Android/.test(navigator.userAgent),
      isChrome: /Chrome/.test(navigator.userAgent),
      hasServiceWorker: 'serviceWorker' in navigator
    })

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleAppInstalled)
    }
  }, [])

  const handleInstallPWA = async () => {
    if (deferredPromptRef.current) {
      deferredPromptRef.current.prompt()
      const { outcome } = await deferredPromptRef.current.userChoice
      if (outcome === 'accepted') {
        setIsPWA(true)
        setShowInstallPrompt(false)
      }
      deferredPromptRef.current = null
    } else {
      alert('Install prompt is not available yet. Please use the browser menu to install or revisit after a bit of usage.');
    }
  }

  const handleCheckUpdate = async () => {
    setIsCheckingUpdate(true)
    try {
      const hasUpdate = await updateService.checkForUpdates()
      if (hasUpdate) {
        if (confirm('🔄 A new version is available! Update now?')) {
          await updateService.applyUpdate()
        }
      } else {
        alert('✅ You are using the latest version!')
      }
    } catch (error) {
      console.error('Update check failed:', error)
      alert('❌ Failed to check for updates')
    } finally {
      setIsCheckingUpdate(false)
    }
  }

  const handleAction = (action) => {
    if (action) {
      action()
    }
    setIsMobileOpen(false)
  }

  // Debug logging for mobile menu
  if (isMobileOpen) {
    console.log('🍔 Mobile Menu Debug:', {
      user: !!user,
      userEmail: user?.email,
      isAdmin,
      onHome: !!onHome,
      onLoadStories: !!onLoadStories,
      onOfflineManager: !!onOfflineManager,
      onAdminClick: !!onAdminClick,
      onNewStory: !!onNewStory,
      onLogout: !!onLogout
    })
  }

  return (
    <>
      {/* Mobile Hamburger Button */}
      <button 
        className="mobile-menu-btn" 
        onClick={() => setIsMobileOpen(!isMobileOpen)} 
        aria-label="Menu"
      >
        <motion.div
          animate={{ rotate: isMobileOpen ? 90 : 0 }}
          transition={{ duration: 0.3 }}
        >
          {isMobileOpen ? '✕' : '☰'}
        </motion.div>
      </button>

      {/* Desktop Menu (Always visible) */}
      <nav className="desktop-menu">
        {onHome && (
        <button 
          onClick={() => handleAction(onHome)} 
          className="menu-btn"
        >
          🏠 Home
        </button>
        )}
        {onLoadStories && (
        <button 
          onClick={() => handleAction(onLoadStories)} 
          className="menu-btn"
        >
          📚 Load Story
        </button>
        )}
        {onOfflineManager && (
        <button 
          onClick={() => handleAction(onOfflineManager)} 
          className="menu-btn"
        >
          📂 Offline Manager
        </button>
        )}
        {isAdmin && onAdminClick && (
        <button 
          onClick={() => handleAction(onAdminClick)} 
          className="menu-btn admin"
        >
          ⚙️ Admin Panel
        </button>
        )}
        {isPlayingStory && onSaveStory && (
        <button 
          onClick={() => handleAction(onSaveStory)} 
          className="menu-btn primary"
        >
          💾 Save
        </button>
        )}
        {isPlayingStory && onDownloadStory && (
        <button 
          onClick={() => handleAction(onDownloadStory)} 
          className="menu-btn primary"
        >
          📥 Download
        </button>
        )}
        {currentStory?.persistent_path && (
        <button 
          onClick={() => handleAction(onShowFileViewer)} 
          className="menu-btn"
        >
          📄 View File
        </button>
        )}
        {onNewStory && (
        <button 
          onClick={() => handleAction(onNewStory)} 
          className="menu-btn primary"
        >
          ✨ New Story
        </button>
        )}
        <button 
          onClick={handleCheckUpdate} 
          className="menu-btn update"
          disabled={isCheckingUpdate}
          title="Check for updates"
        >
          {isCheckingUpdate ? '⏳' : '🔄'} Update
        </button>
        {onProfile && (
        <button 
          onClick={() => handleAction(onProfile)} 
          className="menu-btn profile"
          title="Account"
        >
          {user?.email?.split('@')[0] || '👤'}
        </button>
        )}
        {onLogout && (
        <button 
          onClick={() => handleAction(onLogout)} 
          className="menu-btn logout"
        >
          🚪 Logout
        </button>
        )}
      </nav>

      {/* Mobile Drawer - rendered via Portal outside app container */}
      {createPortal(
        <AnimatePresence>
          {isMobileOpen && (
            <>
              <motion.div
                className="mobile-overlay"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setIsMobileOpen(false)}
              />
              <motion.div
                className="mobile-drawer"
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              >
                <div className="drawer-header">
                  <h3>Menu</h3>
                  <button 
                    onClick={() => setIsMobileOpen(false)} 
                    className="drawer-close-btn"
                  >
                    ✕
                  </button>
                </div>

                <div className="drawer-content">
                  {user && (
                    <div 
                      className="user-profile-card" 
                      onClick={() => handleAction(onProfile)}
                    >
                      <div className="user-avatar">
                        {user.email?.charAt(0).toUpperCase()}
                      </div>
                      <div className="user-info">
                        <p className="user-email">{user.email}</p>
                        {isAdmin && <span className="user-badge">Admin</span>}
                      </div>
                    </div>
                  )}

                  <div className="section-container">
                    <div>
                      <h4 className="section-header">Navigation</h4>
                      {onHome && (
                        <button 
                          onClick={() => handleAction(onHome)} 
                          className="drawer-btn"
                        >
                          <span className="icon">🏠</span>
                          <span>Home</span>
                        </button>
                      )}
                      {onLoadStories && (
                        <button 
                          onClick={() => handleAction(onLoadStories)} 
                          className="drawer-btn"
                        >
                          <span className="icon">📚</span>
                          <span>Load Saved Story</span>
                        </button>
                      )}
                      {onOfflineManager && (
                        <button 
                          onClick={() => handleAction(onOfflineManager)} 
                          className="drawer-btn"
                        >
                          <span className="icon">📂</span>
                          <span>Offline Manager</span>
                        </button>
                      )}
                      {onNewStory && (
                        <button 
                          onClick={() => handleAction(onNewStory)} 
                          className="drawer-btn"
                        >
                          <span className="icon">✨</span>
                          <span>New Story</span>
                        </button>
                      )}
                      {isPlayingStory && onSaveStory && (
                        <button 
                          onClick={() => handleAction(onSaveStory)} 
                          className="drawer-btn primary"
                        >
                          <span className="icon">💾</span>
                          <span>Save Story</span>
                        </button>
                      )}
                      {isPlayingStory && onDownloadStory && (
                        <button 
                          onClick={() => handleAction(onDownloadStory)} 
                          className="drawer-btn primary"
                        >
                          <span className="icon">📥</span>
                          <span>Download Story</span>
                        </button>
                      )}
                      {currentStory?.persistent_path && (
                        <button 
                          onClick={() => handleAction(onShowFileViewer)} 
                          className="drawer-btn"
                        >
                          <span className="icon">📄</span>
                          <span>View Current File</span>
                        </button>
                      )}
                    </div>

                    {isAdmin && onAdminClick && (
                      <>
                        <div className="section-divider"></div>
                        <div>
                          <h4 className="section-header">Admin</h4>
                          <button 
                            onClick={() => handleAction(onAdminClick)} 
                            className="drawer-btn"
                          >
                            <span className="icon">⚙️</span>
                            <span>Admin Panel</span>
                          </button>
                        </div>
                      </>
                    )}

                    <div className="section-divider"></div>
                    <div>
                      <h4 className="section-header">Account</h4>
                      <button 
                        onClick={() => {
                          handleCheckUpdate();
                          setIsMobileOpen(false);
                        }} 
                        className="drawer-btn"
                        disabled={isCheckingUpdate}
                      >
                        <span className="icon">{isCheckingUpdate ? '⏳' : '🔄'}</span>
                        <span>Check for Updates</span>
                      </button>
                      {!isPWA && (
                        <button 
                          onClick={() => {
                            handleInstallPWA();
                            setIsMobileOpen(false);
                          }} 
                          className="drawer-btn primary"
                        >
                          <span className="icon">📲</span>
                          <span>Install App</span>
                        </button>
                      )}
                      {isPWA && (
                        <div className="status-indicator">
                          <span className="icon">✓</span>
                          <span>App Installed</span>
                        </div>
                      )}
                      {onLogout && (
                        <button 
                          onClick={() => handleAction(onLogout)} 
                          className="drawer-btn"
                        >
                          <span className="icon">🚪</span>
                          <span>Logout</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
      </motion.div>
          </>
          )}
        {/* @ts-ignore */}
        {/* @ts-ignore */}
        </AnimatePresence>,
        document.body
      )}
    </>
  )
}

export default NavigationMenu

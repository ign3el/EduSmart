import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import updateService from '../services/updateService'
import './NavigationMenu.css'

function NavigationMenu({ user, isAdmin, onHome, onNewStory, onLoadStories, onOfflineManager, onAdminClick, onProfile, onLogout, onSaveStory, onDownloadStory, isPlayingStory }) {
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const [isCheckingUpdate, setIsCheckingUpdate] = useState(false)
  const [showInstallPrompt, setShowInstallPrompt] = useState(false)
  const [isPWA, setIsPWA] = useState(false)
  let deferredPrompt = null

  // Handle PWA install prompt
  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault()
      deferredPrompt = e
      setShowInstallPrompt(true)
    }

    const handleAppInstalled = () => {
      setShowInstallPrompt(false)
      setIsPWA(true)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', handleAppInstalled)

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true) {
      setIsPWA(true)
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleAppInstalled)
    }
  }, [])

  const handleInstallPWA = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt()
      const { outcome } = await deferredPrompt.userChoice
      if (outcome === 'accepted') {
        setIsPWA(true)
        setShowInstallPrompt(false)
      }
      deferredPrompt = null
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
      <button className="mobile-menu-toggle" onClick={() => setIsMobileOpen(!isMobileOpen)} aria-label="Menu">
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
          <button onClick={() => handleAction(onHome)} className="nav-item">
            🏠 Home
          </button>
        )}
        {onLoadStories && (
          <button onClick={() => handleAction(onLoadStories)} className="nav-item">
            📚 Load Story
          </button>
        )}
        {onOfflineManager && (
          <button onClick={() => handleAction(onOfflineManager)} className="nav-item">
            📂 Offline Manager
          </button>
        )}
        {isAdmin && onAdminClick && (
          <button onClick={() => handleAction(onAdminClick)} className="nav-item admin">
            ⚙️ Admin Panel
          </button>
        )}
        {isPlayingStory && onSaveStory && (
          <button onClick={() => handleAction(onSaveStory)} className="nav-item accent">
            💾 Save
          </button>
        )}
        {isPlayingStory && onDownloadStory && (
          <button onClick={() => handleAction(onDownloadStory)} className="nav-item accent">
            📥 Download
          </button>
        )}
        {!isPlayingStory && onNewStory && (
          <button onClick={() => handleAction(onNewStory)} className="nav-item accent">
            ✨ New Story
          </button>
        )}
        <button 
          onClick={handleCheckUpdate} 
          className="nav-item update-btn"
          disabled={isCheckingUpdate}
          title="Check for updates"
        >
          {isCheckingUpdate ? '⏳' : '🔄'} Update
        </button>
        {onProfile && (
          <button onClick={() => handleAction(onProfile)} className="nav-item profile-avatar" title="Account">
            {user?.email?.split('@')[0] || '👤'}
          </button>
        )}
        {onLogout && (
          <button onClick={() => handleAction(onLogout)} className="nav-item danger">
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
                className="mobile-menu"
                initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            >
              <div className="mobile-menu-header">
                <h3>Menu</h3>
                <button onClick={() => setIsMobileOpen(false)} className="menu-close">✕</button>
              </div>

              <div className="mobile-menu-content">
                {user && (
                  <div className="menu-user-info" onClick={() => handleAction(onProfile)} style={{cursor: 'pointer'}}>
                    <div className="user-avatar">{user.email?.charAt(0).toUpperCase()}</div>
                    <div className="user-details">
                      <p className="user-email">{user.email}</p>
                      {isAdmin && <span className="admin-badge">Admin</span>}
                    </div>
                  </div>
                )}

                <div className="menu-actions">
                  <div className="menu-section">
                    <h4>Navigation</h4>
                    {onHome ? (
                      <button onClick={() => handleAction(onHome)} className="menu-item">
                        <span className="menu-icon">🏠</span>
                        <span>Home</span>
                      </button>
                    ) : null}
                    {onLoadStories ? (
                      <button onClick={() => handleAction(onLoadStories)} className="menu-item">
                        <span className="menu-icon">📚</span>
                        <span>Load Saved Story</span>
                      </button>
                    ) : null}
                    {onOfflineManager ? (
                      <button onClick={() => handleAction(onOfflineManager)} className="menu-item">
                        <span className="menu-icon">📂</span>
                        <span>Offline Manager</span>
                      </button>
                    ) : null}
                    {onNewStory ? (
                      <button onClick={() => handleAction(onNewStory)} className="menu-item">
                        <span className="menu-icon">✨</span>
                        <span>New Story</span>
                      </button>
                    ) : null}
                    {isPlayingStory && onSaveStory ? (
                      <button onClick={() => handleAction(onSaveStory)} className="menu-item accent">
                        <span className="menu-icon">💾</span>
                        <span>Save Story</span>
                      </button>
                    ) : null}
                    {isPlayingStory && onDownloadStory ? (
                      <button onClick={() => handleAction(onDownloadStory)} className="menu-item accent">
                        <span className="menu-icon">📥</span>
                        <span>Download Story</span>
                      </button>
                    ) : null}
                  </div>

                  {isAdmin && onAdminClick ? (
                    <>
                      <div className="menu-divider"></div>
                      <div className="menu-section">
                        <h4>Admin</h4>
                        <button onClick={() => handleAction(onAdminClick)} className="menu-item">
                          <span className="menu-icon">⚙️</span>
                          <span>Admin Panel</span>
                        </button>
                      </div>
                    </>
                  ) : null}

                  <div className="menu-divider"></div>
                  <div className="menu-section">
                    <h4>Account</h4>
                    <button 
                      onClick={() => {
                        handleCheckUpdate();
                        setIsMobileOpen(false);
                      }} 
                      className="menu-item"
                      disabled={isCheckingUpdate}
                    >
                      <span className="menu-icon">{isCheckingUpdate ? '⏳' : '🔄'}</span>
                      <span>Check for Updates</span>
                    </button>
                    {showInstallPrompt && !isPWA && (
                      <button onClick={() => {
                        handleInstallPWA();
                        setIsMobileOpen(false);
                      }} className="menu-item accent">
                        <span className="menu-icon">📲</span>
                        <span>Install App</span>
                      </button>
                    )}
                    {isPWA && (
                      <div className="menu-item" style={{opacity: 0.6}}>
                        <span className="menu-icon">✓</span>
                        <span>App Installed</span>
                      </div>
                    )}
                    {onLogout ? (
                      <button onClick={() => handleAction(onLogout)} className="menu-item danger">
                        <span className="menu-icon">🚪</span>
                        <span>Logout</span>
                      </button>
                    ) : (
                      <div style={{padding: '1rem', color: 'red'}}>ERROR: No logout function</div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          </>
          )}
        </AnimatePresence>,
        document.body
      )}
    </>
  )
}

export default NavigationMenu

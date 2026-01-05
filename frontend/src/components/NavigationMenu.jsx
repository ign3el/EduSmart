import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import updateService from '../services/updateService'

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
        className="fixed top-4 right-4 z-[1000] w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 border-none text-white text-xl cursor-pointer shadow-lg shadow-purple-500/40 flex items-center justify-center transition-all duration-300 hover:scale-105 hover:shadow-purple-500/60 md:hidden" 
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
      <nav className="hidden md:flex items-center gap-2 flex-wrap">
        {onHome && (
          <button 
            onClick={() => handleAction(onHome)} 
            className="px-4 py-2 bg-white/5 border border-purple-500/30 rounded-lg text-ink-1 text-sm font-semibold cursor-pointer transition-all duration-200 hover:bg-purple-500/15 hover:border-purple-500/50 hover:-translate-y-0.5 whitespace-nowrap"
          >
            🏠 Home
          </button>
        )}
        {onLoadStories && (
          <button 
            onClick={() => handleAction(onLoadStories)} 
            className="px-4 py-2 bg-white/5 border border-purple-500/30 rounded-lg text-ink-1 text-sm font-semibold cursor-pointer transition-all duration-200 hover:bg-purple-500/15 hover:border-purple-500/50 hover:-translate-y-0.5 whitespace-nowrap"
          >
            📚 Load Story
          </button>
        )}
        {onOfflineManager && (
          <button 
            onClick={() => handleAction(onOfflineManager)} 
            className="px-4 py-2 bg-white/5 border border-purple-500/30 rounded-lg text-ink-1 text-sm font-semibold cursor-pointer transition-all duration-200 hover:bg-purple-500/15 hover:border-purple-500/50 hover:-translate-y-0.5 whitespace-nowrap"
          >
            📂 Offline Manager
          </button>
        )}
        {isAdmin && onAdminClick && (
          <button 
            onClick={() => handleAction(onAdminClick)} 
            className="px-4 py-2 bg-white/5 border border-cyan-500/40 rounded-lg text-ink-1 text-sm font-semibold cursor-pointer transition-all duration-200 hover:bg-cyan-500/15 hover:border-cyan-500/60 hover:-translate-y-0.5 whitespace-nowrap"
          >
            ⚙️ Admin Panel
          </button>
        )}
        {isPlayingStory && onSaveStory && (
          <button 
            onClick={() => handleAction(onSaveStory)} 
            className="px-4 py-2 bg-gradient-to-br from-purple-500 to-pink-500 border-transparent rounded-lg text-white text-sm font-semibold cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-purple-500/40 hover:-translate-y-0.5 whitespace-nowrap"
          >
            💾 Save
          </button>
        )}
        {isPlayingStory && onDownloadStory && (
          <button 
            onClick={() => handleAction(onDownloadStory)} 
            className="px-4 py-2 bg-gradient-to-br from-purple-500 to-pink-500 border-transparent rounded-lg text-white text-sm font-semibold cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-purple-500/40 hover:-translate-y-0.5 whitespace-nowrap"
          >
            📥 Download
          </button>
        )}
        {currentStory?.persistent_path && (
          <button 
            onClick={() => handleAction(onShowFileViewer)} 
            className="px-4 py-2 bg-white/5 border border-green-500/30 rounded-lg text-ink-1 text-sm font-semibold cursor-pointer transition-all duration-200 hover:bg-green-500/15 hover:border-green-500/50 hover:-translate-y-0.5 whitespace-nowrap"
          >
            📄 View File
          </button>
        )}
        {!isPlayingStory && onNewStory && (
          <button 
            onClick={() => handleAction(onNewStory)} 
            className="px-4 py-2 bg-gradient-to-br from-purple-500 to-pink-500 border-transparent rounded-lg text-white text-sm font-semibold cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-purple-500/40 hover:-translate-y-0.5 whitespace-nowrap"
          >
            ✨ New Story
          </button>
        )}
        <button 
          onClick={handleCheckUpdate} 
          className="px-4 py-2 bg-blue-500/8 border border-blue-500/40 rounded-lg text-ink-1 text-sm font-semibold cursor-pointer transition-all duration-200 hover:bg-blue-500/15 hover:border-blue-500/60 hover:-translate-y-0.5 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isCheckingUpdate}
          title="Check for updates"
        >
          {isCheckingUpdate ? '⏳' : '🔄'} Update
        </button>
        {onProfile && (
          <button 
            onClick={() => handleAction(onProfile)} 
            className="min-w-[40px] h-10 px-3.2 rounded-[20px] bg-gradient-to-br from-purple-500 to-pink-500 border-2 border-white/20 text-white text-[0.85rem] font-bold cursor-pointer transition-all duration-200 hover:scale-110 hover:shadow-lg hover:shadow-purple-500/50 flex items-center justify-center whitespace-nowrap"
            title="Account"
          >
            {user?.email?.split('@')[0] || '👤'}
          </button>
        )}
        {onLogout && (
          <button 
            onClick={() => handleAction(onLogout)} 
            className="px-4 py-2 bg-white/5 border border-rose-500/40 rounded-lg text-ink-1 text-sm font-semibold cursor-pointer transition-all duration-200 hover:bg-rose-500/15 hover:border-rose-500/60 hover:-translate-y-0.5 hover:text-rose-500 whitespace-nowrap"
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
                className="fixed inset-0 bg-black/60 backdrop-blur-[4px] z-[9998]"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setIsMobileOpen(false)}
              />
              <motion.div
                className="fixed top-0 right-0 bottom-0 w-[min(85vw,320px)] bg-gradient-to-br from-[#0f1642] to-[#121f4d] border-l border-purple-500/30 shadow-[-10px_0_40px_rgba(0,0,0,0.5)] z-[9999] flex flex-col overflow-hidden"
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              >
                <div className="flex justify-between items-center p-5 border-b border-purple-500/20 bg-purple-500/10">
                  <h3 className="m-0 text-[1.3rem] text-ink-1 font-bold">Menu</h3>
                  <button 
                    onClick={() => setIsMobileOpen(false)} 
                    className="bg-none border-none text-ink-2 text-[1.5rem] cursor-pointer p-1 transition-colors duration-200 hover:text-ink-1"
                  >
                    ✕
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
                  {user && (
                    <div 
                      className="flex items-center gap-3 p-3 bg-purple-500/8 rounded-lg mx-0 mb-2.5 cursor-pointer" 
                      onClick={() => handleAction(onProfile)}
                    >
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-[1.3rem] font-bold text-white flex-shrink-0">
                        {user.email?.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="m-0 text-[0.95rem] text-ink-1 font-semibold truncate">{user.email}</p>
                        {isAdmin && <span className="inline-block px-2 py-0.5 bg-gradient-to-br from-cyan-500 to-blue-500 text-white rounded-[12px] text-[0.75rem] font-bold mt-1">Admin</span>}
                      </div>
                    </div>
                  )}

                  <div className="flex flex-col flex-1">
                    <div className="px-0 mb-4">
                      <h4 className="m-0 mb-3 px-2 text-[0.85rem] text-ink-2 font-semibold uppercase tracking-wider">Navigation</h4>
                      {onHome ? (
                        <button 
                          onClick={() => handleAction(onHome)} 
                          className="w-full flex items-center gap-3 px-3 py-2.5 bg-white/3 border border-purple-500/15 rounded-[10px] text-ink-1 font-semibold cursor-pointer transition-all duration-200 hover:bg-purple-500/15 hover:border-purple-500/40 hover:translate-x-1 mb-2 text-left"
                        >
                          <span className="text-[1.3rem] w-6 text-center flex-shrink-0">🏠</span>
                          <span>Home</span>
                        </button>
                      ) : null}
                      {onLoadStories ? (
                        <button 
                          onClick={() => handleAction(onLoadStories)} 
                          className="w-full flex items-center gap-3 px-3 py-2.5 bg-white/3 border border-purple-500/15 rounded-[10px] text-ink-1 font-semibold cursor-pointer transition-all duration-200 hover:bg-purple-500/15 hover:border-purple-500/40 hover:translate-x-1 mb-2 text-left"
                        >
                          <span className="text-[1.3rem] w-6 text-center flex-shrink-0">📚</span>
                          <span>Load Saved Story</span>
                        </button>
                      ) : null}
                      {onOfflineManager ? (
                        <button 
                          onClick={() => handleAction(onOfflineManager)} 
                          className="w-full flex items-center gap-3 px-3 py-2.5 bg-white/3 border border-purple-500/15 rounded-[10px] text-ink-1 font-semibold cursor-pointer transition-all duration-200 hover:bg-purple-500/15 hover:border-purple-500/40 hover:translate-x-1 mb-2 text-left"
                        >
                          <span className="text-[1.3rem] w-6 text-center flex-shrink-0">📂</span>
                          <span>Offline Manager</span>
                        </button>
                      ) : null}
                      {onNewStory ? (
                        <button 
                          onClick={() => handleAction(onNewStory)} 
                          className="w-full flex items-center gap-3 px-3 py-2.5 bg-white/3 border border-purple-500/15 rounded-[10px] text-ink-1 font-semibold cursor-pointer transition-all duration-200 hover:bg-purple-500/15 hover:border-purple-500/40 hover:translate-x-1 mb-2 text-left"
                        >
                          <span className="text-[1.3rem] w-6 text-center flex-shrink-0">✨</span>
                          <span>New Story</span>
                        </button>
                      ) : null}
                      {isPlayingStory && onSaveStory ? (
                        <button 
                          onClick={() => handleAction(onSaveStory)} 
                          className="w-full flex items-center gap-3 px-3 py-2.5 bg-gradient-to-br from-purple-500 to-pink-500 border-transparent rounded-[10px] text-white font-semibold cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-purple-500/40 hover:translate-x-1 mb-2 text-left"
                        >
                          <span className="text-[1.3rem] w-6 text-center flex-shrink-0">💾</span>
                          <span>Save Story</span>
                        </button>
                      ) : null}
                      {isPlayingStory && onDownloadStory ? (
                        <button 
                          onClick={() => handleAction(onDownloadStory)} 
                          className="w-full flex items-center gap-3 px-3 py-2.5 bg-gradient-to-br from-purple-500 to-pink-500 border-transparent rounded-[10px] text-white font-semibold cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-purple-500/40 hover:translate-x-1 mb-2 text-left"
                        >
                          <span className="text-[1.3rem] w-6 text-center flex-shrink-0">📥</span>
                          <span>Download Story</span>
                        </button>
                      ) : null}
                      {currentStory?.persistent_path ? (
                        <button 
                          onClick={() => handleAction(onShowFileViewer)} 
                          className="w-full flex items-center gap-3 px-3 py-2.5 bg-white/3 border border-green-500/30 rounded-[10px] text-ink-1 font-semibold cursor-pointer transition-all duration-200 hover:bg-green-500/15 hover:border-green-500/50 hover:translate-x-1 mb-2 text-left"
                        >
                          <span className="text-[1.3rem] w-6 text-center flex-shrink-0">📄</span>
                          <span>View Current File</span>
                        </button>
                      ) : null}
                    </div>

                    {isAdmin && onAdminClick ? (
                      <>
                        <div className="h-px bg-purple-500/15 my-4"></div>
                        <div className="px-0 mb-4">
                          <h4 className="m-0 mb-3 px-2 text-[0.85rem] text-ink-2 font-semibold uppercase tracking-wider">Admin</h4>
                          <button 
                            onClick={() => handleAction(onAdminClick)} 
                            className="w-full flex items-center gap-3 px-3 py-2.5 bg-white/3 border border-purple-500/15 rounded-[10px] text-ink-1 font-semibold cursor-pointer transition-all duration-200 hover:bg-purple-500/15 hover:border-purple-500/40 hover:translate-x-1 text-left"
                          >
                            <span className="text-[1.3rem] w-6 text-center flex-shrink-0">⚙️</span>
                            <span>Admin Panel</span>
                          </button>
                        </div>
                      </>
                    ) : null}

                    <div className="h-px bg-purple-500/15 my-4"></div>
                    <div className="px-0">
                      <h4 className="m-0 mb-3 px-2 text-[0.85rem] text-ink-2 font-semibold uppercase tracking-wider">Account</h4>
                      <button 
                        onClick={() => {
                          handleCheckUpdate();
                          setIsMobileOpen(false);
                        }} 
                        className="w-full flex items-center gap-3 px-3 py-2.5 bg-white/3 border border-purple-500/15 rounded-[10px] text-ink-1 font-semibold cursor-pointer transition-all duration-200 hover:bg-purple-500/15 hover:border-purple-500/40 hover:translate-x-1 mb-2 text-left disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isCheckingUpdate}
                      >
                        <span className="text-[1.3rem] w-6 text-center flex-shrink-0">{isCheckingUpdate ? '⏳' : '🔄'}</span>
                        <span>Check for Updates</span>
                      </button>
                      {!isPWA && (
                        <button 
                          onClick={() => {
                            handleInstallPWA();
                            setIsMobileOpen(false);
                          }} 
                          className="w-full flex items-center gap-3 px-3 py-2.5 bg-gradient-to-br from-purple-500 to-pink-500 border-transparent rounded-[10px] text-white font-semibold cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-purple-500/40 hover:translate-x-1 mb-2 text-left"
                        >
                          <span className="text-[1.3rem] w-6 text-center flex-shrink-0">📲</span>
                          <span>Install App</span>
                        </button>
                      )}
                      {isPWA && (
                        <div className="w-full flex items-center gap-3 px-3 py-2.5 bg-white/3 border border-purple-500/15 rounded-[10px] text-ink-1 font-semibold opacity-60 mb-2">
                          <span className="text-[1.3rem] w-6 text-center flex-shrink-0">✓</span>
                          <span>App Installed</span>
                        </div>
                      )}
                      {onLogout ? (
                        <button 
                          onClick={() => handleAction(onLogout)} 
                          className="w-full flex items-center gap-3 px-3 py-2.5 bg-white/3 border border-rose-500/30 rounded-[10px] text-ink-1 font-semibold cursor-pointer transition-all duration-200 hover:bg-rose-500/15 hover:border-rose-500/50 hover:translate-x-1 hover:text-rose-500 text-left"
                        >
                          <span className="text-[1.3rem] w-6 text-center flex-shrink-0">🚪</span>
                          <span>Logout</span>
                        </button>
                      ) : (
                        <div className="p-4 text-red-500">ERROR: No logout function</div>
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

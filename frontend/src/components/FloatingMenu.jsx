import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import './FloatingMenu.css'

function FloatingMenu({ user, isAdmin, onHome, onNewStory, onLoadStories, onOfflineManager, onSaveOnline, onDownloadOffline, onAdminClick, onLogout, showStoryActions = false }) {
  const [isOpen, setIsOpen] = useState(false)

  const toggleMenu = () => setIsOpen(!isOpen)

  const handleAction = (action) => {
    if (action) {
      action()
    }
    setIsOpen(false)
  }

  return (
    <>
      <button className="floating-menu-toggle" onClick={toggleMenu} aria-label="Menu">
        <span className="menu-text">Menu</span>
        <motion.div
          className="menu-icon"
          animate={{ rotate: isOpen ? 90 : 0 }}
          transition={{ duration: 0.3 }}
        >
          {isOpen ? '✕' : '☰'}
        </motion.div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              className="floating-menu-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              className="floating-menu"
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            >
              <div className="floating-menu-header">
                <h3>Menu</h3>
                <button onClick={() => setIsOpen(false)} className="menu-close">✕</button>
              </div>

              <div className="floating-menu-content">
                {user && (
                  <div className="menu-user-info">
                    <div className="user-avatar">{user.email?.charAt(0).toUpperCase()}</div>
                    <div className="user-details">
                      <p className="user-email">{user.email}</p>
                      {isAdmin && <span className="admin-badge">Admin</span>}
                    </div>
                  </div>
                )}

                <div className="menu-actions">
                  {showStoryActions && (
                    <>
                      <div className="menu-section">
                        <h4>Story Actions</h4>
                        {onSaveOnline && (
                          <button onClick={() => handleAction(onSaveOnline)} className="menu-item">
                            <span className="menu-icon">💾</span>
                            <span>Save Online</span>
                          </button>
                        )}
                        {onDownloadOffline && (
                          <button onClick={() => handleAction(onDownloadOffline)} className="menu-item">
                            <span className="menu-icon">📥</span>
                            <span>Download Offline</span>
                          </button>
                        )}
                        {onNewStory && (
                          <button onClick={() => handleAction(onNewStory)} className="menu-item">
                            <span className="menu-icon">✨</span>
                            <span>New Story</span>
                          </button>
                        )}
                      </div>
                      <div className="menu-divider"></div>
                    </>
                  )}

                  <div className="menu-section">
                    <h4>Navigation</h4>
                    {onHome && (
                      <button onClick={() => handleAction(onHome)} className="menu-item">
                        <span className="menu-icon">🏠</span>
                        <span>Home</span>
                      </button>
                    )}
                    {onLoadStories && (
                      <button onClick={() => handleAction(onLoadStories)} className="menu-item">
                        <span className="menu-icon">📚</span>
                        <span>Load Saved Story</span>
                      </button>
                    )}
                    {onOfflineManager && (
                      <button onClick={() => handleAction(onOfflineManager)} className="menu-item">
                        <span className="menu-icon">📂</span>
                        <span>Offline Manager</span>
                      </button>
                    )}
                  </div>

                  {isAdmin && onAdminClick && (
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
                  )}

                  <div className="menu-divider"></div>
                  <div className="menu-section">
                    <h4>Account</h4>
                    {onLogout && (
                      <button onClick={() => handleAction(onLogout)} className="menu-item danger">
                        <span className="menu-icon">🚪</span>
                        <span>Logout</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}

export default FloatingMenu

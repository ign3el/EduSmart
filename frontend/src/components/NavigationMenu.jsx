import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import './NavigationMenu.css'

function NavigationMenu({ user, isAdmin, onHome, onNewStory, onLoadStories, onOfflineManager, onAdminClick, onLogout }) {
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  const handleAction = (action) => {
    if (action) {
      action()
    }
    setIsMobileOpen(false)
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
        {onNewStory && (
          <button onClick={() => handleAction(onNewStory)} className="nav-item accent">
            ✨ New Story
          </button>
        )}
        {onLogout && (
          <button onClick={() => handleAction(onLogout)} className="nav-item danger">
            🚪 Logout
          </button>
        )}
      </nav>

      {/* Mobile Drawer */}
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
                  <div className="menu-user-info">
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
                    {onNewStory && (
                      <button onClick={() => handleAction(onNewStory)} className="menu-item">
                        <span className="menu-icon">✨</span>
                        <span>New Story</span>
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

export default NavigationMenu

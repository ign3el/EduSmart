import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import './AvatarSelector.css'

function AvatarSelector({ onSelect }) {
  const [avatars, setAvatars] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchAvatars() {
      try {
        setLoading(true)
        const response = await fetch('/api/avatars')
        if (!response.ok) {
          throw new Error('Failed to fetch avatars')
        }
        const data = await response.json()
        // Add frontend-specific properties like emoji and color
        const enhancedAvatars = data.avatars.map(avatar => ({
          ...avatar,
          emoji: getEmojiForAvatar(avatar.id),
          color: getColorForAvatar(avatar.id)
        }));
        setAvatars(enhancedAvatars)
      } catch (error) {
        console.error("Error fetching avatars:", error)
        // Fallback to a default avatar in case of an error
        setAvatars([{ id: 'wizard', name: 'Wise Wizard', description: 'A magical teacher', emoji: '🧙‍♂️', color: '#8b5cf6' }])
      } finally {
        setLoading(false)
      }
    }
    fetchAvatars()
  }, [])

  const handleSelect = (avatar) => {
    setSelected(avatar.id)
    setTimeout(() => {
      onSelect(avatar)
    }, 500)
  }

  if (loading) {
    return (
      <div className="avatar-selector">
        <h2>🎭 Choose Your Guide</h2>
        <div className="loading-spinner-small"></div>
        <p>Loading guides...</p>
      </div>
    )
  }

  return (
    <div className="avatar-selector">
      <h2>🎭 Choose Your Guide</h2>
      <p className="subtitle">Pick a character who will teach you today!</p>

      <div className="avatar-grid">
        {avatars.map((avatar, index) => (
          <motion.div
            key={avatar.id}
            className={`avatar-card ${selected === avatar.id ? 'selected' : ''}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => handleSelect(avatar)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div 
              className="avatar-emoji"
              style={{ background: `${avatar.color}20` }}
            >
              <span>{avatar.emoji}</span>
            </div>
            <h3>{avatar.name}</h3>
            <p>{avatar.description}</p>
            {selected === avatar.id && (
              <motion.div 
                className="selected-badge"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
              >
                ✓
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  )
}

// Helper functions to map backend data to frontend visuals
const getEmojiForAvatar = (id) => {
  const map = {
    wizard: '🧙‍♂️',
    robot: '🤖',
    squirrel: '🐿️',
    astronaut: '👨‍🚀',
    dinosaur: '🦕',
  }
  return map[id] || '👤'
}

const getColorForAvatar = (id) => {
  const map = {
    wizard: '#8b5cf6',
    robot: '#3b82f6',
    squirrel: '#f59e0b',
    astronaut: '#06b6d4',
    dinosaur: '#10b981',
  }
  return map[id] || '#64748b'
}

export default AvatarSelector

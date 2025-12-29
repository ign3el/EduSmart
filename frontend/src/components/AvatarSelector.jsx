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
        
        // FIX: Ensure data is an array before mapping
        // This handles both [{}, {}] and { avatars: [{}, {}] } formats
        const rawList = Array.isArray(data) ? data : (data.avatars || []);
        
        const enhancedAvatars = rawList.map(avatar => ({
          ...avatar,
          // Ensure we have a fallback emoji and color if backend IDs don't match
          emoji: getEmojiForAvatar(avatar.id),
          color: getColorForAvatar(avatar.id)
        }));
        
        setAvatars(enhancedAvatars)
      } catch (error) {
        console.error("Error fetching avatars:", error)
        // Fallback to a default list so the UI doesn't break
        setAvatars([
          { id: 'wizard', name: 'Professor Paws', description: 'Expert Guide', emoji: '🧙‍♂️', color: '#8b5cf6' },
          { id: 'robot', name: 'Robo-Buddy', description: 'Tech Specialist', emoji: '🤖', color: '#3b82f6' }
        ])
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
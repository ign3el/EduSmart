import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import './AvatarSelector.css'

const avatars = [
  {
    id: 'wizard',
    name: 'Wise Wizard',
    description: 'A magical teacher who makes learning enchanting',
    emoji: '🧙‍♂️',
    color: '#8b5cf6'
  },
  {
    id: 'robot',
    name: 'Friendly Robot',
    description: 'A helpful AI companion who loves technology',
    emoji: '🤖',
    color: '#3b82f6'
  },
  {
    id: 'squirrel',
    name: 'Smart Squirrel',
    description: 'A clever forest friend full of wisdom',
    emoji: '🐿️',
    color: '#f59e0b'
  },
  {
    id: 'astronaut',
    name: 'Space Explorer',
    description: 'A cosmic guide to the universe of knowledge',
    emoji: '👨‍🚀',
    color: '#06b6d4'
  },
  {
    id: 'dinosaur',
    name: 'Dino Teacher',
    description: 'A prehistoric professor with ancient wisdom',
    emoji: '🦕',
    color: '#10b981'
  }
]

function AvatarSelector({ onSelect }) {
  const [selected, setSelected] = useState(null)

  const handleSelect = (avatar) => {
    setSelected(avatar.id)
    setTimeout(() => {
      onSelect(avatar)
    }, 500)
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

export default AvatarSelector

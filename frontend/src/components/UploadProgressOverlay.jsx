import { motion } from 'framer-motion'
import './UploadProgressOverlay.css'

function UploadProgressOverlay({ progress, fileName, isVisible }) {
  if (!isVisible) return null

  return (
    <motion.div 
      className="upload-progress-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div 
        className="progress-container"
        initial={{ scale: 0.8, y: 20 }}
        animate={{ scale: 1, y: 0 }}
      >
        <div className="progress-icon">
          {progress === 100 ? (
            <motion.div 
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="checkmark"
            >
              ✓
            </motion.div>
          ) : (
            <motion.div 
              className="uploading-icon"
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            >
              ⬆️
            </motion.div>
          )}
        </div>

        <h3>{progress === 100 ? 'Upload Complete!' : 'Uploading...'}</h3>
        <p>{fileName}</p>

        {/* Progress Bar */}
        <div className="progress-bar-wrapper">
          <div className="progress-bar-container">
            <motion.div 
              className="progress-bar-fill"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            ></motion.div>
          </div>
          <div className="progress-percentage">
            <motion.span
              key={progress}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              {progress}%
            </motion.span>
          </div>
        </div>

        {/* Status Text */}
        <p className="status-text">
          {progress === 100 
            ? '✓ File uploaded successfully' 
            : `${Math.round(progress)}% complete`}
        </p>
      </motion.div>
    </motion.div>
  )
}

export default UploadProgressOverlay

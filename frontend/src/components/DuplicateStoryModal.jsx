import { motion, AnimatePresence } from 'framer-motion';
import './DuplicateStoryModal.css';

function DuplicateStoryModal({ isOpen, onClose, onLoadExisting, onCreateNew, duplicateInfo }) {
  if (!isOpen || !duplicateInfo) return null;

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffHours < 1) {
      return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            className="duplicate-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            className="duplicate-modal"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            <div className="duplicate-header">
              <div className="duplicate-icon">🔍</div>
              <h2>Story Already Exists!</h2>
              <button onClick={onClose} className="duplicate-close">✕</button>
            </div>

            <div className="duplicate-content">
              <div className="duplicate-info-card">
                <p className="duplicate-message">
                  This file was already uploaded and processed recently.
                </p>
                
                <div className="duplicate-details">
                  <div className="detail-item">
                    <span className="detail-label">Created by</span>
                    <span className="detail-value">{duplicateInfo.created_by}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Created</span>
                    <span className="detail-value">{formatDate(duplicateInfo.created_at)}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Story Title</span>
                    <span className="detail-value">{duplicateInfo.story_title}</span>
                  </div>
                </div>
              </div>

              <div className="duplicate-actions">
                <button onClick={onLoadExisting} className="load-existing-button">
                  <span className="button-icon">📖</span>
                  <div className="button-content">
                    <span className="button-title">Load Existing Story</span>
                    <span className="button-subtitle">View the already generated story</span>
                  </div>
                </button>

                <button onClick={onCreateNew} className="create-new-button">
                  <span className="button-icon">✨</span>
                  <div className="button-content">
                    <span className="button-title">Create New Story</span>
                    <span className="button-subtitle">Generate a fresh version</span>
                  </div>
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default DuplicateStoryModal;

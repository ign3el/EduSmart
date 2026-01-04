import './StoryActionsBar.css'

function StoryActionsBar({ onSaveOnline, onDownloadOffline, isSaved, isOffline }) {
  if (!onSaveOnline && !onDownloadOffline) {
    return null
  }

  return (
    <div className="story-actions-bar">
      {!isSaved && !isOffline && onSaveOnline && (
        <button onClick={onSaveOnline} className="story-action-btn save">
          💾 Save Online
        </button>
      )}
      {!isOffline && onDownloadOffline && (
        <button onClick={onDownloadOffline} className="story-action-btn download">
          📥 Download Offline
        </button>
      )}
    </div>
  )
}

export default StoryActionsBar

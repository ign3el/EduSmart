import './StoryActionsBar.css'

function StoryActionsBar({ onSaveOnline, onDownloadOffline, isSaved, isOffline, allScenesReady = false }) {
  if (!onSaveOnline && !onDownloadOffline) {
    return null
  }

  return (
    <div className="story-actions-bar">
      {!isSaved && !isOffline && onSaveOnline && (
        <button onClick={onSaveOnline} className="story-action-btn save" disabled={!allScenesReady}>
          💾 Save Online {!allScenesReady && '(Generating...)'}
        </button>
      )}
      {!isOffline && onDownloadOffline && (
        <button onClick={onDownloadOffline} className="story-action-btn download" disabled={!allScenesReady}>
          📥 Download Offline {!allScenesReady && '(Generating...)'}
        </button>
      )}
    </div>
  )
}

export default StoryActionsBar

import React, { useState } from 'react';
import './AdminPanel.css';
import StoryList from './StoryList';
import JobStatusViewer from './JobStatusViewer';
import TtsLab from './TtsLab'; // Import the new component
import './TtsLab.css'; // Import its CSS

const AdminPanel = ({ onPlayStory, onBack }) => {
    const [activeTab, setActiveTab] = useState('stories');

    return (
        <div className="admin-panel">
            <header className="admin-panel-header">
                <div className="admin-panel-header-top">
                    <h1>Admin Panel</h1>
                    <button onClick={onBack} className="admin-back-button">← Back to Home</button>
                </div>
                <nav className="admin-panel-nav">
                    <button 
                        className={`admin-nav-button ${activeTab === 'stories' ? 'active' : ''}`}
                        onClick={() => setActiveTab('stories')}
                    >
                        User Stories
                    </button>
                    <button 
                        className={`admin-nav-button ${activeTab === 'jobs' ? 'active' : ''}`}
                        onClick={() => setActiveTab('jobs')}
                    >
                        Job Status
                    </button>
                    <button 
                        className={`admin-nav-button ${activeTab === 'tts-lab' ? 'active' : ''}`}
                        onClick={() => setActiveTab('tts-lab')}
                    >
                        TTS Playground
                    </button>
                </nav>
            </header>
            <main className="admin-panel-content">
                {activeTab === 'stories' && <StoryList onPlayStory={onPlayStory} />}
                {activeTab === 'jobs' && <JobStatusViewer />}
                {activeTab === 'tts-lab' && <TtsLab />}
            </main>
        </div>
    );
};

export default AdminPanel;

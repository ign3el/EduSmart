import React, { useState, useEffect } from 'react';
import apiClient from '../services/api';
import './AdminDashboard.css'; // Assuming we will create this file for styling

const AdminDashboard = ({ onPlayStory, onBack, onNavigateToDbViewer }) => {
  const [stories, setStories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAllStories = async () => {
      setIsLoading(true);
      setError('');
      try {
        const response = await apiClient.get('/api/list-stories');
        setStories(response.data);
      } catch (err) {
        setError('Failed to load stories. You may not have admin privileges.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAllStories();
  }, []);

  const handlePlay = async (storyId) => {
    try {
        const response = await apiClient.get(`/api/load-story/${storyId}`);
        if (response.data) {
            // This callback is passed from App.jsx to set the main state
            onPlayStory(response.data.story_data, response.data.name, storyId);
        }
    } catch (err) {
        setError(`Failed to load story ${storyId}. It may have been deleted.`);
        console.error(err);
    }
  };

  if (isLoading) {
    return <div className="loading-message">Loading all stories...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h2>Admin Dashboard</h2>
        <div>
          <button onClick={onNavigateToDbViewer} className="db-viewer-button">View Job State DB</button>
          <button onClick={onBack} className="back-button">← Back to Home</button>
        </div>
      </div>
      <p>Viewing all stories created by all users.</p>
      <div className="admin-table-container">
        <table>
          <thead>
            <tr>
              <th>Story Name</th>
              <th>Created By</th>
              <th>Date Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {stories.length === 0 ? (
              <tr>
                <td colSpan="4">No stories have been created yet.</td>
              </tr>
            ) : (
              stories.map(story => (
                <tr key={story.story_id || story.id}>
                  <td>{story.name}</td>
                  <td>{story.username || 'N/A'}</td>
                  <td>{new Date(story.created_at).toLocaleString()}</td>
                  <td>
                    <button 
                      className="play-button"
                      onClick={() => handlePlay(story.story_id)}
                    >
                      Play Story
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminDashboard;

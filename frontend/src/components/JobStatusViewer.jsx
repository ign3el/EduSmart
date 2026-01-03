import React, { useState, useEffect, useMemo } from 'react';
import { getJobStateTableData } from '../services/api';
import './JobStatusViewer.css';

const JobStatusViewer = () => {
    const [jobs, setJobs] = useState([]);
    const [scenes, setScenes] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [expandedJobs, setExpandedJobs] = useState({});

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            setError('');
            try {
                // Fetch both tables in parallel
                const [jobsResponse, scenesResponse] = await Promise.all([
                    getJobStateTableData('stories'),
                    getJobStateTableData('scenes')
                ]);
                setJobs(jobsResponse.content || []);
                setScenes(scenesResponse.content || []);
            } catch (err) {
                setError('Failed to load job status data.');
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, []);

    const scenesByJobId = useMemo(() => {
        return scenes.reduce((acc, scene) => {
            (acc[scene.story_id] = acc[scene.story_id] || []).push(scene);
            return acc;
        }, {});
    }, [scenes]);

    const toggleJobExpansion = (jobId) => {
        setExpandedJobs(prev => ({ ...prev, [jobId]: !prev[jobId] }));
    };

    const StatusPill = ({ status }) => (
        <span className={`status-pill status-${status}`}>{status}</span>
    );
    
    const SceneStatusIcon = ({ status }) => {
        let icon, text;
        switch (status) {
            case 'completed':
                icon = '✅';
                text = 'Completed';
                break;
            case 'processing':
                icon = '⏳';
                text = 'Processing';
                break;
            case 'failed':
                icon = '❌';
                text = 'Failed';
                break;
            default:
                icon = '⚪';
                text = 'Pending';
        }
        return <span title={text}>{icon}</span>;
    };


    if (isLoading) {
        return <div className="loading-message">Loading job statuses...</div>;
    }

    if (error) {
        return <div className="error-message">{error}</div>;
    }

    return (
        <div className="job-status-viewer">
            <div className="job-table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Status</th>
                            <th>Job Title</th>
                            <th>Progress</th>
                            <th>Created At</th>
                            <th>Story ID</th>
                        </tr>
                    </thead>
                    <tbody>
                        {jobs.length === 0 ? (
                            <tr>
                                <td colSpan="5">No jobs found.</td>
                            </tr>
                        ) : (
                            jobs.map(job => (
                                <React.Fragment key={job.story_id}>
                                    <tr className="job-row" onClick={() => toggleJobExpansion(job.story_id)}>
                                        <td><StatusPill status={job.status} /></td>
                                        <td>{job.title}</td>
                                        <td>
                                            <div className="progress-bar-container">
                                                <div 
                                                    className="progress-bar-inner" 
                                                    style={{ width: `${job.total_scenes > 0 ? (job.completed_scenes / job.total_scenes) * 100 : 0}%` }}
                                                ></div>
                                            </div>
                                            {job.completed_scenes} / {job.total_scenes} Scenes
                                        </td>
                                        <td>{new Date(job.created_at).toLocaleString()}</td>
                                        <td className="job-id-cell">{job.story_id}</td>
                                    </tr>
                                    {expandedJobs[job.story_id] && (
                                        <tr className="scene-details-row">
                                            <td colSpan="5">
                                                <div className="scene-details-container">
                                                    <h4>Scenes for: {job.title}</h4>
                                                    <ul>
                                                        {(scenesByJobId[job.story_id] || []).map(scene => (
                                                            <li key={scene.scene_id}>
                                                                <strong>Scene {scene.scene_index + 1}:</strong>
                                                                <span className="scene-status">
                                                                    Image: <SceneStatusIcon status={scene.image_status} />
                                                                </span>
                                                                <span className="scene-status">
                                                                    Audio: <SceneStatusIcon status={scene.audio_status} />
                                                                </span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default JobStatusViewer;

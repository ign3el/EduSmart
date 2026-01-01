import { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import './Auth.css';

export default function Login({ onSwitchToSignup, onSuccess }) {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [apiError, setApiError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError('');

    if (!formData.email || !formData.password) {
      setApiError('Email and password are required.');
      return;
    }

    setLoading(true);
    try {
      await login(formData.email, formData.password);
      if (onSuccess) onSuccess();
    } catch (err) {
      if (err.response) {
        // Handle specific HTTP status codes from the API
        switch (err.response.status) {
          case 401:
            setApiError('Incorrect email or password.');
            break;
          case 403:
            setApiError('Email has not been verified. Please check your inbox.');
            break;
          default:
            // For other errors, show the detail message from the API if it exists
            setApiError(err.response.data?.detail || 'An unexpected error occurred.');
        }
      } else {
        // Handle network errors where there is no response
        setApiError('Could not connect to the server. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div className="auth-container" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
      <div className="auth-box">
        <h2>Welcome Back</h2>
        <form onSubmit={handleSubmit} noValidate>
          <div className="input-group">
            <input
              type="email"
              name="email"
              placeholder="Email"
              autoComplete="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>
          <div className="input-group">
            <input
              type="password"
              name="password"
              placeholder="Password"
              autoComplete="current-password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>
          
          {apiError && <p className="auth-error">{apiError}</p>}
          
          <button type="submit" disabled={loading} className="auth-button">
            {loading ? 'Logging In...' : 'Login'}
          </button>
        </form>
        <p className="auth-switch">
          Don't have an account? <a onClick={onSwitchToSignup}>Sign Up</a>
        </p>
      </div>
    </motion.div>
  );
}
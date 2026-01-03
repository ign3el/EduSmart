import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import './Auth.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('verifying'); // verifying, success, error
  const [message, setMessage] = useState('');
  const token = searchParams.get('token');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('Invalid verification link. Please check your email for the correct link.');
      return;
    }

    const verifyEmail = async () => {
      try {
        await axios.get(`${API_URL}/api/auth/verify-email?token=${token}`);
        setStatus('success');
        setMessage('Your email has been verified successfully! You can now log in to your account.');
      } catch (err) {
        setStatus('error');
        if (err.response?.data?.detail) {
          setMessage(err.response.data.detail);
        } else {
          setMessage('Failed to verify email. The link may have expired.');
        }
      }
    };

    verifyEmail();
  }, [token, navigate]);

  const handleResendEmail = async () => {
    // This would require the user's email, which we don't have here
    // You might want to redirect to a page where they can enter their email
    navigate('/resend-verification');
  };

  return (
    <div className="auth-page">
      <motion.div
        className="auth-container"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <div className={`auth-box verify-box ${status}`}>
          {status === 'verifying' && (
            <>
              <div className="spinner"></div>
              <h2>Verifying Your Email</h2>
              <p>Please wait while we verify your email address...</p>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="success-icon">✓</div>
              <h2>Email Verified!</h2>
              <p>{message}</p>
              <button
                className="auth-button"
                onClick={() => navigate('/')}
                style={{ marginTop: '20px' }}
              >
                Go to Login
              </button>
            </>
          )}

          {status === 'error' && (
            <>
              <div className="error-icon">✕</div>
              <h2>Verification Failed</h2>
              <p>{message}</p>
              <div className="verify-actions">
                <button
                  className="auth-button"
                  onClick={() => navigate('/login')}
                >
                  Go to Login
                </button>
                <button
                  className="auth-button-secondary"
                  onClick={handleResendEmail}
                >
                  Resend Verification Email
                </button>
              </div>
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
}

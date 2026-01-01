import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import './Auth.css';

// A validation utility function to check form data
const validate = (formData) => {
  const errors = {};
  if (!formData.username) {
    errors.username = 'Username is required.';
  } else if (formData.username.length < 3) {
    errors.username = 'Username must be at least 3 characters.';
  } else if (formData.username.length > 50) {
    errors.username = 'Username must be 50 characters or less.';
  }
  
  if (!formData.email) {
    errors.email = 'Email is required.';
  } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
    errors.email = 'Email address is invalid.';
  }

  if (!formData.password) {
    errors.password = 'Password is required.';
  } else if (formData.password.length < 6) {
    errors.password = 'Password must be at least 6 characters.';
  } else if (formData.password.length > 100) {
    errors.password = 'Password must be 100 characters or less.';
  }

  if (!formData.passwordConfirm) {
    errors.passwordConfirm = 'Please confirm your password.';
  } else if (formData.password !== formData.passwordConfirm) {
    errors.passwordConfirm = 'Passwords do not match.';
  }

  return errors;
};

export default function Signup({ onSwitchToLogin, onSuccess }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    passwordConfirm: '',
  });
  
  // State for validation errors that appear next to inputs
  const [fieldErrors, setFieldErrors] = useState({});
  // State for a general API error message shown above the button
  const [apiError, setApiError] = useState('');
  
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();

  // Re-validate the form whenever the user types
  useEffect(() => {
    // Only show errors after the user has started typing
    if (Object.values(formData).some(val => val !== '')) {
      setFieldErrors(validate(formData));
    }
  }, [formData]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError('');
    
    // Perform a final validation check on submit
    const validationErrors = validate(formData);
    setFieldErrors(validationErrors);
    
    // If there are any errors, stop the form submission
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setLoading(true);
    try {
      await signup(formData.username, formData.email, formData.password);
      if (onSuccess) onSuccess(); // Trigger success callback (e.g., show a message)
    } catch (err) {
      // Handle API errors (e.g., duplicate email/username)
      if (err.response && err.response.status === 409) {
        setApiError('An account with this email or username already exists.');
      } else {
        // Generic error for other issues
        setApiError(err.response?.data?.detail || 'An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div className="auth-container" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
      <div className="auth-box">
        <h2>Create Account</h2>
        <form onSubmit={handleSubmit} noValidate>
          <div className="input-group">
            <input
              type="text"
              name="username"
              placeholder="Username"
              value={formData.username}
              onChange={handleChange}
              required
              className={fieldErrors.username ? 'input-error' : ''}
            />
            {fieldErrors.username && <p className="auth-validation-error">{fieldErrors.username}</p>}
          </div>
          
          <div className="input-group">
            <input
              type="email"
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleChange}
              required
              className={fieldErrors.email ? 'input-error' : ''}
            />
            {fieldErrors.email && <p className="auth-validation-error">{fieldErrors.email}</p>}
          </div>

          <div className="input-group">
            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              required
              className={fieldErrors.password ? 'input-error' : ''}
            />
            {fieldErrors.password && <p className="auth-validation-error">{fieldErrors.password}</p>}
          </div>

          <div className="input-group">
            <input
              type="password"
              name="passwordConfirm"
              placeholder="Confirm Password"
              value={formData.passwordConfirm}
              onChange={handleChange}
              required
              className={fieldErrors.passwordConfirm ? 'input-error' : ''}
            />
            {fieldErrors.passwordConfirm && <p className="auth-validation-error">{fieldErrors.passwordConfirm}</p>}
          </div>
          
          {apiError && <p className="auth-error">{apiError}</p>}
          
          <button type="submit" disabled={loading} className="auth-button">
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>
        <p className="auth-switch">
          Already have an account? <a onClick={onSwitchToLogin}>Login</a>
        </p>
      </div>
    </motion.div>
  );
}
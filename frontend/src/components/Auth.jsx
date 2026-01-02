import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Login from './Login';
import Signup from './Signup';
import './Auth.css';

export default function Auth() {
  const [activeTab, setActiveTab] = useState('login');

  return (
    <div className="auth-page">
      <motion.div
        className="auth-wrapper"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="auth-header">
          <h1>EduSmart</h1>
          <p>Transform learning into magical adventures</p>
        </div>

        <div className="auth-tabs">
          <button
            className={`auth-tab ${activeTab === 'login' ? 'active' : ''}`}
            onClick={() => setActiveTab('login')}
          >
            Login
          </button>
          <button
            className={`auth-tab ${activeTab === 'signup' ? 'active' : ''}`}
            onClick={() => setActiveTab('signup')}
          >
            Sign Up
          </button>
        </div>

        <AnimatePresence mode="wait">
          {activeTab === 'login' ? (
            <Login
              key="login"
              onSwitchToSignup={() => setActiveTab('signup')}
            />
          ) : (
            <Signup
              key="signup"
              onSwitchToLogin={() => setActiveTab('login')}
            />
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}

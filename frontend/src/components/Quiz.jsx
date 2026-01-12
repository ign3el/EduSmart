import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { markQuizComplete } from '../services/api';
import './Quiz.css';

const Quiz = ({ questions, onComplete, onBackToStory, storyId }) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [score, setScore] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [selectedOption, setSelectedOption] = useState(null);
  const [isCorrect, setIsCorrect] = useState(null);
  const [userAnswers, setUserAnswers] = useState([]);
  const [reviewMode, setReviewMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Handle missing or invalid quiz data
  const validQuestions = Array.isArray(questions) && questions.length > 0 ? questions : [];

  // Fallback: Generate quiz from story data if quiz is missing
  const generateFallbackQuiz = () => {
    console.log('🔄 Generating fallback quiz from available data...');
    // This would be called if questions are missing
    // For now, we'll show a message
  };

  // Check for quiz data issues
  React.useEffect(() => {
    if (!questions || !Array.isArray(questions) || questions.length === 0) {
      console.warn('⚠️ Quiz component received no questions data');
      console.log('Expected: Array of question objects');
      console.log('Received:', questions);
    }
  }, [questions]);

  const retakeQuiz = () => {
    setCurrentQuestion(0);
    setScore(0);
    setShowResults(false);
    setSelectedOption(null);
    setIsCorrect(null);
    setUserAnswers([]);
    setReviewMode(false);
  };

  const handleAnswer = (option) => {
    if (selectedOption !== null) return; // Prevent double clicking

    setSelectedOption(option);
    const currentQ = questions[currentQuestion];
    // Handle both old and new quiz structure
    const correctAnswer = currentQ.correct_answer || currentQ.answer;
    const questionText = currentQ.question_text || currentQ.question;
    const correct = option === correctAnswer;
    setIsCorrect(correct);

    // Track user answer with proper state update
    const newAnswer = {
      question: questionText,
      selected: option,
      correct: correctAnswer,
      explanation: currentQ.explanation || "No explanation provided.",
      isCorrect: correct,
      // Include additional metadata if available
      source: currentQ.source,
      document_section: currentQ.document_section
    };

    setUserAnswers(prev => [...prev, newAnswer]);
    if (correct) {
      setScore(prev => prev + 1);
    }

    setTimeout(async () => {
      if (currentQuestion + 1 < questions.length) {
        setCurrentQuestion(currentQuestion + 1);
        setSelectedOption(null);
        setIsCorrect(null);
      } else {
        setShowResults(true);
        // Mark quiz as completed
        if (storyId) {
          try {
            await markQuizComplete(storyId);
            console.log('✓ Quiz marked as completed');
          } catch (error) {
            console.error('Failed to mark quiz complete:', error);
          }
        }
      }
    }, 1500);
  };

  if (showResults && !reviewMode) {
    return (
      <motion.div className="quiz-container results" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h2>🎉 Learning Complete!</h2>
        <div className="score-circle">
          <span>{score}</span> / {questions.length}
        </div>
        <p>{score === questions.length ? "Perfect Score! Excellent work!" : "Great job! Keep learning!"}</p>
        <div className="result-buttons">
          <button onClick={retakeQuiz} className="retake-btn">🔄 Retake Quiz</button>
          <button onClick={() => setReviewMode(true)} className="review-btn">📖 Review Answers</button>
          {onBackToStory && <button onClick={onBackToStory} className="story-btn">📖 Back to Story</button>}
          <button onClick={onComplete} className="finish-btn">Back to Library</button>
        </div>
      </motion.div>
    );
  }

  if (reviewMode) {
    return (
      <motion.div className="quiz-container review-mode" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h2>📖 Answer Review</h2>
        <div className="review-list">
          {userAnswers.map((answer, index) => (
            <motion.div
              key={index}
              className={`review-item ${answer.isCorrect ? 'correct-answer' : 'wrong-answer'}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div className="review-header">
                <span className="review-number">Question {index + 1}</span>
                <span className={`review-badge ${answer.isCorrect ? 'badge-correct' : 'badge-wrong'}`}>
                  {answer.isCorrect ? '✓ Correct' : '✗ Wrong'}
                </span>
                {answer.source && (
                  <span className="source-badge">
                    {answer.source === 'extracted' ? '📄 From Document' : '🧠 Generated'}
                  </span>
                )}
              </div>
              <h4>{answer.question}</h4>
              <div className="review-answers">
                <p className="user-answer">
                  <strong>Your answer:</strong>
                  <span className={answer.isCorrect ? 'text-correct' : 'text-wrong'}>
                    {answer.selected}
                  </span>
                </p>
                {!answer.isCorrect && (
                  <p className="correct-answer-text">
                    <strong>Correct answer:</strong>
                    <span className="text-correct">{answer.correct}</span>
                  </p>
                )}
              </div>
              {answer.document_section && (
                <div className="document-section">
                  <strong>📍 Section:</strong> {answer.document_section}
                </div>
              )}
              <div className="explanation">
                <strong>💡 Explanation:</strong>
                <p>{answer.explanation}</p>
              </div>
            </motion.div>
          ))}
        </div>
        <div className="review-footer">
          <div className="final-score">
            Final Score: <strong>{score} / {questions.length}</strong>
            ({Math.round((score / questions.length) * 100)}%)
          </div>
          {onBackToStory && <button onClick={onBackToStory} className="story-btn">📖 Back to Story</button>}
          <button onClick={onComplete} className="finish-btn">Back to Library</button>
        </div>
      </motion.div>
    );
  }

  // Guard: Handle missing or invalid questions
  if (!validQuestions.length) {
    return (
      <motion.div
        className="quiz-container error"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="error-state">
          <h2>⚠️ Quiz Unavailable</h2>
          <p>The quiz data for this story is not yet available.</p>
          <p className="small">Please ensure the story generation completed successfully.</p>
          {onBackToStory && <button onClick={onBackToStory} className="finish-btn">Back to Story</button>}
          <button onClick={onComplete} className="finish-btn">Back to Library</button>
        </div>
      </motion.div>
    );
  }

  const q = validQuestions[currentQuestion];
  // Handle both old and new quiz structure
  const questionText = q.question_text || q.question;
  const options = q.options || [];

  return (
    <div className="quiz-container">
      <div className="quiz-progress">
        Question {currentQuestion + 1} of {validQuestions.length}
        {q.source && (
          <span className="source-indicator">
            {q.source === 'extracted' ? '📄' : '🧠'}
          </span>
        )}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={currentQuestion}
          initial={{ x: 50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -50, opacity: 0 }}
          className="question-card"
        >
          <h3>{questionText}</h3>
          {q.document_section && (
            <div className="document-section-info">
              📍 From: {q.document_section}
            </div>
          )}
          <div className="options-grid">
            {options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleAnswer(option)}
                className={`option-btn ${selectedOption === option
                  ? (isCorrect ? 'correct' : 'wrong')
                  : ''
                  }`}
                disabled={selectedOption !== null}
              >
                {option}
              </button>
            ))}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default Quiz;

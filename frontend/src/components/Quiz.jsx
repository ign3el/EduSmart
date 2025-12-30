import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './Quiz.css';

const Quiz = ({ questions, onComplete }) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [score, setScore] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [selectedOption, setSelectedOption] = useState(null);
  const [isCorrect, setIsCorrect] = useState(null);
  const [userAnswers, setUserAnswers] = useState([]);
  const [reviewMode, setReviewMode] = useState(false);

  const handleAnswer = (option) => {
    if (selectedOption !== null) return; // Prevent double clicking

    setSelectedOption(option);
    const correct = option === questions[currentQuestion].answer;
    setIsCorrect(correct);

    // Track user answer
    setUserAnswers([...userAnswers, {
      question: questions[currentQuestion].question,
      selected: option,
      correct: questions[currentQuestion].answer,
      explanation: questions[currentQuestion].explanation || "No explanation available.",
      isCorrect: correct
    }]);

    if (correct) setScore(score + 1);

    setTimeout(() => {
      if (currentQuestion + 1 < questions.length) {
        setCurrentQuestion(currentQuestion + 1);
        setSelectedOption(null);
        setIsCorrect(null);
      } else {
        setShowResults(true);
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
          <button onClick={() => setReviewMode(true)} className="review-btn">📖 Review Answers</button>
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
          <button onClick={onComplete} className="finish-btn">Back to Library</button>
        </div>
      </motion.div>
    );
  }

  const q = questions[currentQuestion];

  return (
    <div className="quiz-container">
      <div className="quiz-progress">
        Question {currentQuestion + 1} of {questions.length}
      </div>
      
      <AnimatePresence mode="wait">
        <motion.div 
          key={currentQuestion}
          initial={{ x: 50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -50, opacity: 0 }}
          className="question-card"
        >
          <h3>{q.question}</h3>
          <div className="options-grid">
            {q.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleAnswer(option)}
                className={`option-btn ${
                  selectedOption === option 
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
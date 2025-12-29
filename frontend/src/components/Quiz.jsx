import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './Quiz.css';

const Quiz = ({ questions, onComplete }) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [score, setScore] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [selectedOption, setSelectedOption] = useState(null);
  const [isCorrect, setIsCorrect] = useState(null);

  const handleAnswer = (option) => {
    if (selectedOption !== null) return; // Prevent double clicking

    setSelectedOption(option);
    const correct = option === questions[currentQuestion].answer;
    setIsCorrect(correct);

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

  if (showResults) {
    return (
      <motion.div className="quiz-container results" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h2>🎉 Learning Complete!</h2>
        <div className="score-circle">
          <span>{score}</span> / {questions.length}
        </div>
        <p>{score === questions.length ? "Perfect Score! You're a Desert Expert!" : "Great job! Keep learning!"}</p>
        <button onClick={onComplete} className="finish-btn">Back to Library</button>
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
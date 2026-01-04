/**
 * Progress Steps Component
 * Accessible progress indicator for multi-step forms
 */

import React from 'react';

function ProgressSteps({ steps, currentStep, onStepClick }) {
  return (
    <div className="progress-container" role="navigation" aria-label="Booking progress">
      <div className="progress-steps">
        {steps.map((step, index) => {
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;
          
          return (
            <div
              key={index}
              className={`progress-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
              aria-current={isActive ? 'step' : undefined}
            >
              <button
                className="progress-step-number"
                onClick={() => isCompleted && onStepClick && onStepClick(index)}
                disabled={!isCompleted}
                aria-label={`Step ${index + 1}: ${step.label}${isCompleted ? ' (completed)' : isActive ? ' (current)' : ''}`}
                tabIndex={isCompleted ? 0 : -1}
              >
                {isCompleted ? (
                  <svg 
                    width="20" 
                    height="20" 
                    viewBox="0 0 24 24" 
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                  </svg>
                ) : (
                  index + 1
                )}
              </button>
              <span className="progress-step-label">{step.label}</span>
            </div>
          );
        })}
      </div>
      
      {/* Progress bar */}
      <div 
        className="progress-bar"
        role="progressbar"
        aria-valuenow={currentStep}
        aria-valuemin={0}
        aria-valuemax={steps.length - 1}
        aria-label={`Step ${currentStep + 1} of ${steps.length}`}
      >
        <div 
          className="progress-bar-fill"
          style={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
        />
      </div>
      
      {/* Screen reader announcement */}
      <div className="sr-only" role="status" aria-live="polite">
        Step {currentStep + 1} of {steps.length}: {steps[currentStep]?.label}
      </div>
    </div>
  );
}

export default ProgressSteps;

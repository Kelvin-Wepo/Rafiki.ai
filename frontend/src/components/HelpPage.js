import React, { useEffect } from 'react';
import { useAccessibility } from '../context/AccessibilityContext';

const HelpPage = () => {
  const { speak } = useAccessibility();

  useEffect(() => {
    speak('Welcome to the help page. Here you will find information on how to use this application with voice commands and accessibility features.');
  }, [speak]);

  const helpSections = [
    {
      title: 'Getting Started',
      icon: '🚀',
      content: [
        'This application helps you access Kenyan government services through voice commands.',
        'You can speak your requests or type them in the chat.',
        'Press the large microphone button to start speaking.',
        'The system will guide you through each service step by step.'
      ]
    },
    {
      title: 'Voice Commands',
      icon: '🎤',
      content: [
        '"Apply for passport" - Start passport application',
        '"Book appointment" - Schedule a service appointment',
        '"Check my bookings" - View your appointments',
        '"Help" - Get assistance at any time',
        '"Cancel" - Cancel current operation',
        '"Repeat" - Hear the last message again'
      ]
    },
    {
      title: 'Keyboard Shortcuts',
      icon: '⌨️',
      content: [
        'Tab - Move to next element',
        'Shift + Tab - Move to previous element',
        'Enter or Space - Activate buttons',
        'Escape - Close dialogs or cancel',
        'Alt + V - Toggle voice input',
        'Alt + H - Toggle high contrast',
        'Alt + Plus - Increase text size',
        'Alt + Minus - Decrease text size'
      ]
    },
    {
      title: 'Available Services',
      icon: '📋',
      content: [
        'National ID Application and Renewal',
        'Passport Application and Renewal',
        'Driving License Services',
        'Certificate of Good Conduct',
        'Business Registration',
        'Land Search Services'
      ]
    },
    {
      title: 'Accessibility Features',
      icon: '♿',
      content: [
        'High Contrast Mode - Better visibility for low vision users',
        'Adjustable Text Size - Make text larger or smaller',
        'Screen Reader Support - Full ARIA labels for screen readers',
        'Voice Output - All responses are spoken aloud',
        'Keyboard Navigation - Full keyboard accessibility',
        'Reduced Motion - Minimize animations if preferred'
      ]
    },
    {
      title: 'SMS Notifications',
      icon: '📱',
      content: [
        'Receive appointment confirmations via SMS',
        'Get reminders before your scheduled appointments',
        'Updates on application status sent to your phone',
        'Make sure to provide a valid Kenyan phone number'
      ]
    },
    {
      title: 'Contact Support',
      icon: '📞',
      content: [
        'For technical support, call: 0800-723-4000',
        'Email: support@ecitizen.go.ke',
        'Visit any Huduma Centre for in-person assistance',
        'Operating hours: Monday to Friday, 8:00 AM - 5:00 PM'
      ]
    }
  ];

  return (
    <main 
      className="help-page"
      role="main"
      aria-labelledby="help-title"
    >
      <div className="container">
        <header className="page-header">
          <h1 id="help-title" tabIndex="-1">
            Help & Accessibility Guide
          </h1>
          <p className="page-description">
            Learn how to use this application with voice commands and accessibility features
          </p>
        </header>

        <div className="help-sections">
          {helpSections.map((section, index) => (
            <section 
              key={index}
              className="help-section"
              aria-labelledby={`section-${index}`}
            >
              <h2 id={`section-${index}`} className="section-title">
                <span className="section-icon" aria-hidden="true">
                  {section.icon}
                </span>
                {section.title}
              </h2>
              <ul className="help-list" role="list">
                {section.content.map((item, itemIndex) => (
                  <li key={itemIndex} className="help-item">
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>

        <section className="quick-tips" aria-labelledby="tips-title">
          <h2 id="tips-title">Quick Tips</h2>
          <div className="tips-grid">
            <div className="tip-card">
              <span className="tip-number" aria-hidden="true">1</span>
              <h3>Speak Clearly</h3>
              <p>Speak at a normal pace and clearly pronounce your words for best recognition.</p>
            </div>
            <div className="tip-card">
              <span className="tip-number" aria-hidden="true">2</span>
              <h3>Listen to Responses</h3>
              <p>The system will speak back all responses. Wait for it to finish before speaking again.</p>
            </div>
            <div className="tip-card">
              <span className="tip-number" aria-hidden="true">3</span>
              <h3>Ask for Help</h3>
              <p>Say "help" at any time to get assistance with the current step.</p>
            </div>
            <div className="tip-card">
              <span className="tip-number" aria-hidden="true">4</span>
              <h3>Prepare Documents</h3>
              <p>Have your ID number and phone ready before starting an application.</p>
            </div>
          </div>
        </section>

        <section className="faq" aria-labelledby="faq-title">
          <h2 id="faq-title">Frequently Asked Questions</h2>
          <div className="faq-list">
            <details className="faq-item">
              <summary>How do I start a voice command?</summary>
              <p>
                Click or tap the large microphone button in the chat area. You'll hear a beep 
                indicating that the system is listening. Speak your request clearly, and the 
                system will process it automatically.
              </p>
            </details>
            <details className="faq-item">
              <summary>What if the system doesn't understand me?</summary>
              <p>
                Try speaking more slowly and clearly. You can also type your request in the 
                text input field. If problems persist, check that your microphone is working 
                and that you've granted microphone permissions.
              </p>
            </details>
            <details className="faq-item">
              <summary>How do I change the text size?</summary>
              <p>
                Use the accessibility controls at the top of the page. Click the "A+" button 
                to increase text size or "A-" to decrease it. You can also use keyboard 
                shortcuts Alt + Plus and Alt + Minus.
              </p>
            </details>
            <details className="faq-item">
              <summary>Will I receive SMS confirmations?</summary>
              <p>
                Yes, once you book an appointment, you'll receive an SMS confirmation to the 
                phone number you provided. You'll also get a reminder before your appointment.
              </p>
            </details>
            <details className="faq-item">
              <summary>Is this service available 24/7?</summary>
              <p>
                The voice assistant is available 24/7. However, some services may only process 
                during business hours. Appointments can only be booked during Huduma Centre 
                operating hours.
              </p>
            </details>
          </div>
        </section>
      </div>

      <style jsx>{`
        .help-page {
          padding: 2rem 1rem;
          min-height: 100vh;
        }

        .container {
          max-width: 1000px;
          margin: 0 auto;
        }

        .page-header {
          text-align: center;
          margin-bottom: 3rem;
        }

        .page-header h1 {
          font-size: 2.5rem;
          margin-bottom: 1rem;
        }

        .page-description {
          font-size: 1.25rem;
          opacity: 0.8;
        }

        .help-sections {
          display: grid;
          gap: 2rem;
        }

        .help-section {
          background: var(--card-bg, white);
          padding: 1.5rem;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .section-title {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 1.5rem;
          margin-bottom: 1rem;
          color: var(--primary-color, #006600);
        }

        .section-icon {
          font-size: 1.75rem;
        }

        .help-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .help-item {
          padding: 0.75rem 0;
          padding-left: 1.5rem;
          position: relative;
          border-bottom: 1px solid var(--border-color, #eee);
        }

        .help-item:last-child {
          border-bottom: none;
        }

        .help-item::before {
          content: '→';
          position: absolute;
          left: 0;
          color: var(--primary-color, #006600);
        }

        .quick-tips {
          margin-top: 3rem;
        }

        .quick-tips h2 {
          text-align: center;
          margin-bottom: 2rem;
        }

        .tips-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 1.5rem;
        }

        .tip-card {
          background: var(--card-bg, white);
          padding: 1.5rem;
          border-radius: 12px;
          text-align: center;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .tip-number {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          height: 40px;
          background: var(--primary-color, #006600);
          color: white;
          border-radius: 50%;
          font-size: 1.25rem;
          font-weight: bold;
          margin-bottom: 1rem;
        }

        .tip-card h3 {
          margin-bottom: 0.5rem;
        }

        .faq {
          margin-top: 3rem;
        }

        .faq h2 {
          text-align: center;
          margin-bottom: 2rem;
        }

        .faq-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .faq-item {
          background: var(--card-bg, white);
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .faq-item summary {
          padding: 1rem 1.5rem;
          cursor: pointer;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .faq-item summary:hover {
          background: var(--hover-bg, #f5f5f5);
        }

        .faq-item summary::marker {
          color: var(--primary-color, #006600);
        }

        .faq-item p {
          padding: 0 1.5rem 1.5rem;
          margin: 0;
          line-height: 1.6;
        }

        .faq-item[open] summary {
          border-bottom: 1px solid var(--border-color, #eee);
        }

        @media (max-width: 768px) {
          .page-header h1 {
            font-size: 1.75rem;
          }

          .section-title {
            font-size: 1.25rem;
          }
        }
      `}</style>
    </main>
  );
};

export default HelpPage;

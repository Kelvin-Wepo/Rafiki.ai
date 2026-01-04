/**
 * Avatar Studio Showcase - Landing Page
 * Displays the Avatar Generator with styling showcase
 */

import React, { useState } from 'react';
import AfricanAvatarGenerator from './AfricanAvatarGenerator';
import './AvatarStudioShowcase.css';

const AvatarStudioShowcase = () => {
  const [showDemo, setShowDemo] = useState(false);

  if (showDemo) {
    return <AfricanAvatarGenerator />;
  }

  return (
    <div className="showcase-container">
      {/* Hero Section */}
      <section className="showcase-hero">
        <div className="hero-content">
          <div className="hero-text">
            <h1>
              <span className="emoji">🎬</span>
              African Avatar Studio
            </h1>
            <p className="hero-subtitle">
              Create stunning talking avatars powered by AI
            </p>
            <p className="hero-description">
              Generate professional African woman avatars with Imagen and create 
              lip-synced talking head videos with SadTalker in minutes.
            </p>

            {/* Features Grid */}
            <div className="features-grid">
              <div className="feature-item">
                <span className="feature-icon">✨</span>
                <h3>AI-Powered</h3>
                <p>Generated with Google Imagen</p>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🎤</span>
                <h3>Lip-Sync Video</h3>
                <p>SadTalker video generation</p>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🎨</span>
                <h3>Fully Customizable</h3>
                <p>Create unique avatars</p>
              </div>
              <div className="feature-item">
                <span className="feature-icon">⚡</span>
                <h3>Fast Generation</h3>
                <p>Minutes, not hours</p>
              </div>
            </div>

            <button 
              className="cta-button"
              onClick={() => setShowDemo(true)}
            >
              Start Creating →
            </button>
          </div>

          {/* Hero Image */}
          <div className="hero-visual">
            <div className="avatar-preview-showcase">
              <div className="avatar-circle">
                <span className="avatar-emoji">👩</span>
              </div>
              <div className="avatar-decoration">
                <span className="decoration-item">✨</span>
                <span className="decoration-item">🎬</span>
                <span className="decoration-item">🎤</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="showcase-features">
        <h2>Create Professional Avatars</h2>
        <div className="features-showcase">
          <div className="showcase-feature">
            <h3>📋 Step 1: Customize</h3>
            <p>Choose skin tone, hair style, clothing, personality, background, and language for your unique avatar</p>
            <div className="showcase-example">
              <div className="example-grid">
                <div className="example-item">Light</div>
                <div className="example-item">Braids</div>
                <div className="example-item">Suit</div>
                <div className="example-item">Warm</div>
              </div>
            </div>
          </div>

          <div className="showcase-feature">
            <h3>🎵 Step 2: Add Audio</h3>
            <p>Upload your speech or audio file in MP3, WAV, or OGG format to synchronize with the avatar</p>
            <div className="showcase-example">
              <div className="audio-preview">
                <span>🎧 Speech.mp3</span>
                <span>2.5 MB</span>
              </div>
            </div>
          </div>

          <div className="showcase-feature">
            <h3>🎬 Step 3: Generate</h3>
            <p>Watch as SadTalker creates a professional talking video with perfect lip-sync</p>
            <div className="showcase-example">
              <div className="video-preview">
                <span>▶️</span>
                <span>Generated Video</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Customization Section */}
      <section className="showcase-customization">
        <h2>Full Customization Options</h2>
        <div className="customization-showcase">
          <div className="customization-row">
            <div className="customization-item">
              <span className="customize-emoji">🟠</span>
              <h4>Skin Tones</h4>
              <p>Light, Medium, Dark</p>
            </div>
            <div className="customization-item">
              <span className="customize-emoji">👩‍🦱</span>
              <h4>Hair Styles</h4>
              <p>Natural, Braids, Twists, Straight</p>
            </div>
            <div className="customization-item">
              <span className="customize-emoji">👔</span>
              <h4>Clothing</h4>
              <p>Professional, Traditional, Casual, Formal</p>
            </div>
            <div className="customization-item">
              <span className="customize-emoji">😊</span>
              <h4>Personality</h4>
              <p>Warm, Professional, Patient, Encouraging</p>
            </div>
            <div className="customization-item">
              <span className="customize-emoji">🏢</span>
              <h4>Backgrounds</h4>
              <p>Office, Traditional, Neutral, Government</p>
            </div>
            <div className="customization-item">
              <span className="customize-emoji">🗣️</span>
              <h4>Languages</h4>
              <p>Kenyan, American, British, Swahili</p>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="showcase-usecases">
        <h2>Perfect For</h2>
        <div className="usecases-grid">
          <div className="usecase-card">
            <span className="usecase-emoji">🎓</span>
            <h3>E-Learning</h3>
            <p>Create engaging training videos with professional presenters</p>
          </div>
          <div className="usecase-card">
            <span className="usecase-emoji">📊</span>
            <h3>Presentations</h3>
            <p>Add visual appeal to reports and business presentations</p>
          </div>
          <div className="usecase-card">
            <span className="usecase-emoji">🏛️</span>
            <h3>Government</h3>
            <p>Facilitate citizen engagement and service announcements</p>
          </div>
          <div className="usecase-card">
            <span className="usecase-emoji">📱</span>
            <h3>Social Media</h3>
            <p>Generate unique content for your social channels</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="showcase-cta">
        <div className="cta-content">
          <h2>Ready to Create?</h2>
          <p>Transform your ideas into professional talking avatars today</p>
          <button 
            className="cta-button cta-button-large"
            onClick={() => setShowDemo(true)}
          >
            Launch Avatar Studio
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="showcase-footer">
        <p>🎬 African Avatar Studio • Powered by Imagen & SadTalker</p>
        <p><small>Create professional talking avatars for presentations, training, and entertainment</small></p>
      </footer>
    </div>
  );
};

export default AvatarStudioShowcase;

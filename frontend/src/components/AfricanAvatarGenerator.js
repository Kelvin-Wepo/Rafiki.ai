/**
 * African Avatar Generator - Modern UI Component
 * Create talking avatars using Imagen + SadTalker
 */

import React, { useState, useRef, useEffect } from 'react';
import './AfricanAvatarGenerator.css';

const AfricanAvatarGenerator = () => {
  // State management
  const [currentStep, setCurrentStep] = useState('customize'); // customize, preview, video, result
  const [avatarConfig, setAvatarConfig] = useState({
    name: 'Amara',
    skin_tone: 'medium',
    hair_style: 'braids',
    clothing: 'professional_suit',
    personality: 'warm_friendly',
    background: 'office',
    language: 'en-KE'
  });

  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  const [audioFile, setAudioFile] = useState(null);
  const [audioPreview, setAudioPreview] = useState(null);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const videoRef = useRef(null);

  // Configuration options
  const configurations = {
    skin_tones: [
      { value: 'light', label: 'Light', emoji: '🟡' },
      { value: 'medium', label: 'Medium', emoji: '🟠' },
      { value: 'dark', label: 'Dark', emoji: '🔴' }
    ],
    hair_styles: [
      { value: 'natural', label: 'Natural', emoji: '👩' },
      { value: 'braids', label: 'Braids', emoji: '👩‍🦱' },
      { value: 'twists', label: 'Twists', emoji: '👩‍🦰' },
      { value: 'straight', label: 'Straight', emoji: '👩‍🦳' }
    ],
    clothing: [
      { value: 'professional_suit', label: 'Professional Suit', emoji: '👔' },
      { value: 'traditional', label: 'Traditional', emoji: '🥻' },
      { value: 'casual', label: 'Casual', emoji: '👕' },
      { value: 'formal', label: 'Formal', emoji: '👗' }
    ],
    personalities: [
      { value: 'warm_friendly', label: 'Warm & Friendly', emoji: '😊' },
      { value: 'professional', label: 'Professional', emoji: '😐' },
      { value: 'patient', label: 'Patient', emoji: '🤗' },
      { value: 'encouraging', label: 'Encouraging', emoji: '😄' }
    ],
    backgrounds: [
      { value: 'office', label: 'Office', emoji: '🏢' },
      { value: 'traditional', label: 'Traditional', emoji: '🏛️' },
      { value: 'neutral', label: 'Neutral', emoji: '⚪' },
      { value: 'government', label: 'Government', emoji: '🏛️' }
    ],
    languages: [
      { value: 'en-KE', label: 'Kenyan English', emoji: '🇰🇪' },
      { value: 'en-US', label: 'American English', emoji: '🇺🇸' },
      { value: 'en-GB', label: 'British English', emoji: '🇬🇧' },
      { value: 'sw-KE', label: 'Swahili', emoji: '🗣️' }
    ]
  };

  // Handle configuration change
  const handleConfigChange = (field, value) => {
    setAvatarConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Generate avatar
  const generateAvatar = async () => {
    try {
      setLoading(true);
      setError(null);
      setProgress(10);

      const response = await fetch('http://localhost:8000/avatar/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(avatarConfig)
      });

      setProgress(50);

      if (!response.ok) {
        throw new Error('Failed to generate avatar');
      }

      const data = await response.json();
      
      if (data.success) {
        setGeneratedImage(data.data);
        setProgress(100);
        setSuccess(true);
        setCurrentStep('preview');
        setTimeout(() => setSuccess(false), 3000);
      } else {
        throw new Error(data.message || 'Avatar generation failed');
      }
    } catch (err) {
      setError(err.message || 'Error generating avatar');
      console.error('Avatar generation error:', err);
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  // Handle audio upload
  const handleAudioUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!['audio/mpeg', 'audio/wav', 'audio/ogg'].includes(file.type)) {
        setError('Please upload an MP3, WAV, or OGG file');
        return;
      }
      setAudioFile(file);
      const url = URL.createObjectURL(file);
      setAudioPreview(url);
      setError(null);
    }
  };

  // Generate talking video
  const generateVideo = async () => {
    if (!generatedImage || !audioFile) {
      setError('Please upload audio and generate avatar first');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setProgress(10);

      const formData = new FormData();
      formData.append('image', new Blob([generatedImage.prompt]), `${avatarConfig.name}.png`);
      formData.append('audio', audioFile);
      formData.append('pose_style', 1);
      formData.append('exp_scale', 1.0);

      setProgress(30);

      const response = await fetch('http://localhost:8000/avatar/generate-talking-video', {
        method: 'POST',
        body: formData
      });

      setProgress(70);

      if (!response.ok) {
        throw new Error('Failed to generate video');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setVideoUrl(url);
      setProgress(100);
      setSuccess(true);
      setCurrentStep('result');
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.message || 'Error generating video');
      console.error('Video generation error:', err);
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  // Download video
  const downloadVideo = () => {
    if (videoUrl) {
      const a = document.createElement('a');
      a.href = videoUrl;
      a.download = `${avatarConfig.name}_avatar.mp4`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  // Reset to start
  const reset = () => {
    setCurrentStep('customize');
    setAudioFile(null);
    setAudioPreview(null);
    setGeneratedImage(null);
    setVideoUrl(null);
    setError(null);
    setSuccess(false);
  };

  return (
    <div className="avatar-generator-container">
      {/* Header */}
      <header className="avatar-header">
        <div className="header-content">
          <h1 className="header-title">
            <span className="header-emoji">🎬</span>
            African Avatar Studio
          </h1>
          <p className="header-subtitle">
            Create beautiful talking avatars with Imagen & SadTalker
          </p>
        </div>
      </header>

      {/* Main Container */}
      <div className="avatar-main">
        {/* Sidebar - Avatar Preview */}
        <aside className="avatar-sidebar">
          <div className="avatar-preview-card">
            <div className="preview-header">
              <h3>Avatar Preview</h3>
            </div>
            
            <div className="avatar-preview-area">
              {generatedImage ? (
                <div className="avatar-generated">
                  <div className="avatar-placeholder-generated">
                    <span className="avatar-icon">👩</span>
                  </div>
                  <div className="avatar-info">
                    <h4>{avatarConfig.name}</h4>
                    <p className="skin-tone-label">
                      {configurations.skin_tones.find(s => s.value === avatarConfig.skin_tone)?.label}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="avatar-placeholder">
                  <div className="avatar-icon-large">👩</div>
                  <p>No avatar yet</p>
                  <small>Generate one to see preview</small>
                </div>
              )}
            </div>

            {/* Quick Stats */}
            {generatedImage && (
              <div className="avatar-stats">
                <div className="stat-item">
                  <span className="stat-emoji">👗</span>
                  <span className="stat-text">
                    {configurations.clothing.find(c => c.value === avatarConfig.clothing)?.label}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-emoji">🗣️</span>
                  <span className="stat-text">
                    {configurations.languages.find(l => l.value === avatarConfig.language)?.label}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-emoji">😊</span>
                  <span className="stat-text">
                    {configurations.personalities.find(p => p.value === avatarConfig.personality)?.label}
                  </span>
                </div>
              </div>
            )}

            {/* Status Indicator */}
            <div className={`status-badge ${generatedImage ? 'ready' : 'pending'}`}>
              <span className="status-dot"></span>
              {generatedImage ? 'Ready for Video' : 'Awaiting Generation'}
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="avatar-content">
          {/* Error Alert */}
          {error && (
            <div className="alert alert-error">
              <span className="alert-icon">⚠️</span>
              <div className="alert-content">
                <strong>Error</strong>
                <p>{error}</p>
              </div>
              <button 
                className="alert-close"
                onClick={() => setError(null)}
              >
                ✕
              </button>
            </div>
          )}

          {/* Success Alert */}
          {success && (
            <div className="alert alert-success">
              <span className="alert-icon">✅</span>
              <p>Success! Your avatar is ready</p>
            </div>
          )}

          {/* Step 1: Customize Avatar */}
          {currentStep === 'customize' && (
            <div className="step-container">
              <div className="step-header">
                <h2>Step 1: Customize Your Avatar</h2>
                <p>Create a unique avatar by selecting appearance attributes</p>
              </div>

              <div className="customization-grid">
                {/* Name Input */}
                <div className="form-group full-width">
                  <label>Avatar Name</label>
                  <input
                    type="text"
                    value={avatarConfig.name}
                    onChange={(e) => handleConfigChange('name', e.target.value)}
                    placeholder="e.g., Amara, Zainab, Fatima"
                    className="form-input"
                  />
                </div>

                {/* Skin Tone */}
                <div className="form-group">
                  <label>Skin Tone</label>
                  <div className="option-buttons">
                    {configurations.skin_tones.map(option => (
                      <button
                        key={option.value}
                        className={`option-btn ${avatarConfig.skin_tone === option.value ? 'active' : ''}`}
                        onClick={() => handleConfigChange('skin_tone', option.value)}
                        title={option.label}
                      >
                        <span className="option-emoji">{option.emoji}</span>
                        <span className="option-label">{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Hair Style */}
                <div className="form-group">
                  <label>Hair Style</label>
                  <div className="option-buttons">
                    {configurations.hair_styles.map(option => (
                      <button
                        key={option.value}
                        className={`option-btn ${avatarConfig.hair_style === option.value ? 'active' : ''}`}
                        onClick={() => handleConfigChange('hair_style', option.value)}
                        title={option.label}
                      >
                        <span className="option-emoji">{option.emoji}</span>
                        <span className="option-label">{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Clothing */}
                <div className="form-group">
                  <label>Clothing Style</label>
                  <div className="option-buttons">
                    {configurations.clothing.map(option => (
                      <button
                        key={option.value}
                        className={`option-btn ${avatarConfig.clothing === option.value ? 'active' : ''}`}
                        onClick={() => handleConfigChange('clothing', option.value)}
                        title={option.label}
                      >
                        <span className="option-emoji">{option.emoji}</span>
                        <span className="option-label">{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Personality */}
                <div className="form-group">
                  <label>Personality</label>
                  <div className="option-buttons">
                    {configurations.personalities.map(option => (
                      <button
                        key={option.value}
                        className={`option-btn ${avatarConfig.personality === option.value ? 'active' : ''}`}
                        onClick={() => handleConfigChange('personality', option.value)}
                        title={option.label}
                      >
                        <span className="option-emoji">{option.emoji}</span>
                        <span className="option-label">{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Background */}
                <div className="form-group">
                  <label>Background</label>
                  <div className="option-buttons">
                    {configurations.backgrounds.map(option => (
                      <button
                        key={option.value}
                        className={`option-btn ${avatarConfig.background === option.value ? 'active' : ''}`}
                        onClick={() => handleConfigChange('background', option.value)}
                        title={option.label}
                      >
                        <span className="option-emoji">{option.emoji}</span>
                        <span className="option-label">{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Language */}
                <div className="form-group">
                  <label>Language / Accent</label>
                  <div className="option-buttons">
                    {configurations.languages.map(option => (
                      <button
                        key={option.value}
                        className={`option-btn ${avatarConfig.language === option.value ? 'active' : ''}`}
                        onClick={() => handleConfigChange('language', option.value)}
                        title={option.label}
                      >
                        <span className="option-emoji">{option.emoji}</span>
                        <span className="option-label">{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Generate Button */}
              <div className="button-group">
                <button
                  className="btn btn-primary btn-lg"
                  onClick={generateAvatar}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span className="spinner"></span>
                      Generating Avatar...
                    </>
                  ) : (
                    <>
                      <span className="btn-icon">✨</span>
                      Generate Avatar
                    </>
                  )}
                </button>
              </div>

              {/* Progress Bar */}
              {loading && (
                <div className="progress-container">
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                  </div>
                  <p className="progress-text">{progress}% Complete</p>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Preview & Upload Audio */}
          {currentStep === 'preview' && (
            <div className="step-container">
              <div className="step-header">
                <h2>Step 2: Upload Audio</h2>
                <p>Upload your speech or audio file to create the talking video</p>
              </div>

              <div className="audio-upload-area">
                <div className="upload-box">
                  <input
                    type="file"
                    id="audio-input"
                    accept="audio/mpeg,audio/wav,audio/ogg"
                    onChange={handleAudioUpload}
                    style={{ display: 'none' }}
                  />
                  <label htmlFor="audio-input" className="upload-label">
                    <div className="upload-icon">🎵</div>
                    <h3>Upload Audio File</h3>
                    <p>MP3, WAV, or OGG format</p>
                    <button className="btn btn-secondary">Choose File</button>
                  </label>
                </div>

                {/* Audio Preview */}
                {audioFile && (
                  <div className="audio-preview-box">
                    <div className="audio-info">
                      <span className="audio-icon">🎧</span>
                      <div className="audio-details">
                        <p className="audio-filename">{audioFile.name}</p>
                        <p className="audio-size">{(audioFile.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                    <audio controls className="audio-player">
                      <source src={audioPreview} type={audioFile.type} />
                      Your browser does not support the audio element.
                    </audio>
                    <button
                      className="btn-remove"
                      onClick={() => {
                        setAudioFile(null);
                        setAudioPreview(null);
                      }}
                    >
                      ✕ Remove
                    </button>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="button-group button-group-spread">
                <button
                  className="btn btn-secondary"
                  onClick={() => setCurrentStep('customize')}
                >
                  ← Back
                </button>
                <button
                  className="btn btn-primary btn-lg"
                  onClick={generateVideo}
                  disabled={!audioFile || loading}
                >
                  {loading ? (
                    <>
                      <span className="spinner"></span>
                      Generating Video...
                    </>
                  ) : (
                    <>
                      <span className="btn-icon">🎬</span>
                      Generate Video
                    </>
                  )}
                </button>
              </div>

              {/* Progress Bar */}
              {loading && (
                <div className="progress-container">
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                  </div>
                  <p className="progress-text">{progress}% Complete</p>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Video Result */}
          {currentStep === 'result' && (
            <div className="step-container">
              <div className="step-header">
                <h2>Step 3: Your Talking Avatar</h2>
                <p>Preview and download your generated talking avatar video</p>
              </div>

              {videoUrl && (
                <div className="video-result-area">
                  <div className="video-container">
                    <video
                      ref={videoRef}
                      controls
                      autoPlay
                      className="video-player"
                    >
                      <source src={videoUrl} type="video/mp4" />
                      Your browser does not support the video tag.
                    </video>
                  </div>

                  <div className="result-info">
                    <div className="result-title">
                      <h3>{avatarConfig.name}'s Talking Avatar</h3>
                      <p className="result-subtitle">Generated with Imagen + SadTalker</p>
                    </div>

                    <div className="result-stats">
                      <div className="stat">
                        <span className="stat-icon">👤</span>
                        <span className="stat-name">Avatar</span>
                        <span className="stat-value">{avatarConfig.name}</span>
                      </div>
                      <div className="stat">
                        <span className="stat-icon">🎤</span>
                        <span className="stat-name">Audio Format</span>
                        <span className="stat-value">{audioFile?.type.split('/')[1].toUpperCase()}</span>
                      </div>
                      <div className="stat">
                        <span className="stat-icon">🌍</span>
                        <span className="stat-name">Language</span>
                        <span className="stat-value">{configurations.languages.find(l => l.value === avatarConfig.language)?.label}</span>
                      </div>
                      <div className="stat">
                        <span className="stat-icon">✅</span>
                        <span className="stat-name">Status</span>
                        <span className="stat-value">Complete</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="button-group button-group-spread">
                <button
                  className="btn btn-secondary"
                  onClick={reset}
                >
                  🔄 Create Another
                </button>
                <button
                  className="btn btn-primary btn-lg"
                  onClick={downloadVideo}
                >
                  <span className="btn-icon">💾</span>
                  Download Video
                </button>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="avatar-footer">
        <p>
          🎬 African Avatar Studio • Powered by Imagen & SadTalker
          <br />
          <small>Create beautiful, professional talking avatars for presentations, training, and more</small>
        </p>
      </footer>
    </div>
  );
};

export default AfricanAvatarGenerator;

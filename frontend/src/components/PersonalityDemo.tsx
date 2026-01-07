/**
 * Comprehensive Personality Demo
 * Showcases all avatar personalities with comparison and testing
 */
import React, { useState, useEffect } from 'react';
import { RafikiSadTalkerAvatar } from './avatar';
import { useSadTalker } from '../hooks';
import './PersonalityDemo.css';

interface Personality {
  name: string;
  description: string;
  expression_scale: number;
  still_mode: boolean;
}

interface PersonalityResponse {
  success: boolean;
  current_personality: string;
  personalities: Record<string, Personality>;
}

const SAMPLE_TEXTS = [
  { label: 'Greeting', text: 'Hello! Welcome to eCitizen services. How can I help you today?' },
  { label: 'Instructions', text: 'Please have your ID number ready. I will guide you through the passport application process step by step.' },
  { label: 'Apology', text: 'I sincerely apologize for the inconvenience. Let me help you resolve this issue right away.' },
  { label: 'Celebration', text: 'Congratulations! Your application has been successfully submitted. You should receive confirmation shortly.' },
  { label: 'Information', text: 'The eCitizen platform provides access to over 300 government services online. You can apply for passports, IDs, business permits, and much more.' }
];

export const PersonalityDemo: React.FC = () => {
  const [personalities, setPersonalities] = useState<Record<string, Personality>>({});
  const [selectedPersonality, setSelectedPersonality] = useState<string>('friendly');
  const [selectedText, setSelectedText] = useState<string>(SAMPLE_TEXTS[0].text);
  const [currentPersonality, setCurrentPersonality] = useState<string>('friendly');
  const [comparisonMode, setComparisonMode] = useState<boolean>(false);
  const [comparePersonalities, setComparePersonalities] = useState<string[]>(['friendly', 'professional']);
  const [loading, setLoading] = useState<boolean>(false);

  const {
    generateFromText,
    currentVideoUrl,
    currentAudioUrl,
    isFallbackMode,
    isGenerating,
    error
  } = useSadTalker({
    backendUrl: 'http://localhost:8000',
    avatarId: 'rafiki_avatar'
  });

  // Fetch available personalities
  useEffect(() => {
    const fetchPersonalities = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/avatar/personality');
        const data: PersonalityResponse = await response.json();
        
        if (data.success) {
          setPersonalities(data.personalities);
          setCurrentPersonality(data.current_personality);
        }
      } catch (err) {
        console.error('Failed to fetch personalities:', err);
      }
    };

    fetchPersonalities();
  }, []);

  // Set personality on backend
  const setPersonalityOnBackend = async (personality: string) => {
    try {
      const formData = new FormData();
      formData.append('personality', personality);
      
      const response = await fetch('http://localhost:8000/api/avatar/personality', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      if (data.success) {
        setCurrentPersonality(personality);
      }
    } catch (err) {
      console.error('Failed to set personality:', err);
    }
  };

  // Generate video with selected personality
  const handleGenerate = async () => {
    setLoading(true);
    await setPersonalityOnBackend(selectedPersonality);
    await generateFromText(selectedText);
    setLoading(false);
  };

  // Generate comparison
  const handleCompare = async () => {
    // For now, just generate with first personality
    // In a full implementation, would generate multiple videos
    setLoading(true);
    await setPersonalityOnBackend(comparePersonalities[0]);
    await generateFromText(selectedText);
    setLoading(false);
  };

  return (
    <div className="personality-demo">
      <header className="demo-header">
        <h1>🎭 Avatar Personality Demo</h1>
        <p>Explore different personality modes and see how Rafiki's expressions change</p>
      </header>

      <div className="demo-content">
        {/* Personality Grid */}
        <section className="personalities-section">
          <h2>Available Personalities</h2>
          <div className="personality-grid">
            {Object.entries(personalities).map(([name, data]) => (
              <div
                key={name}
                className={`personality-card ${selectedPersonality === name ? 'selected' : ''} ${currentPersonality === name ? 'active' : ''}`}
                onClick={() => setSelectedPersonality(name)}
              >
                <h3>{name}</h3>
                <p className="description">{data.description}</p>
                <div className="stats">
                  <span className="stat">
                    Expression: {(data.expression_scale * 100).toFixed(0)}%
                  </span>
                  <span className="stat">
                    {data.still_mode ? '🔒 Still Mode' : '🔓 Dynamic'}
                  </span>
                </div>
                {currentPersonality === name && (
                  <div className="active-badge">Currently Active</div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Sample Text Selection */}
        <section className="text-section">
          <h2>Sample Texts</h2>
          <div className="text-selector">
            {SAMPLE_TEXTS.map((sample) => (
              <button
                key={sample.label}
                className={`text-button ${selectedText === sample.text ? 'selected' : ''}`}
                onClick={() => setSelectedText(sample.text)}
              >
                {sample.label}
              </button>
            ))}
          </div>
          <textarea
            className="text-input"
            value={selectedText}
            onChange={(e) => setSelectedText(e.target.value)}
            placeholder="Or type your own text..."
            rows={4}
          />
        </section>

        {/* Mode Toggle */}
        <section className="mode-section">
          <div className="mode-toggle">
            <button
              className={`mode-button ${!comparisonMode ? 'active' : ''}`}
              onClick={() => setComparisonMode(false)}
            >
              Single View
            </button>
            <button
              className={`mode-button ${comparisonMode ? 'active' : ''}`}
              onClick={() => setComparisonMode(true)}
            >
              Comparison View
            </button>
          </div>
        </section>

        {/* Comparison Selector */}
        {comparisonMode && (
          <section className="comparison-selector">
            <h3>Select Personalities to Compare</h3>
            <div className="compare-checkboxes">
              {Object.keys(personalities).map((name) => (
                <label key={name} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={comparePersonalities.includes(name)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setComparePersonalities([...comparePersonalities, name]);
                      } else {
                        setComparePersonalities(comparePersonalities.filter(p => p !== name));
                      }
                    }}
                  />
                  {name}
                </label>
              ))}
            </div>
          </section>
        )}

        {/* Generation Controls */}
        <section className="controls-section">
          <button
            className="generate-button"
            onClick={comparisonMode ? handleCompare : handleGenerate}
            disabled={loading || isGenerating || !selectedText}
          >
            {loading || isGenerating ? 'Generating...' : comparisonMode ? 'Compare Personalities' : 'Generate with Personality'}
          </button>
          {error && <div className="error-message">{error}</div>}
        </section>

        {/* Avatar Display */}
        <section className="avatar-section">
          {!comparisonMode ? (
            <div className="single-avatar">
              <h3>Preview: {selectedPersonality}</h3>
              <RafikiSadTalkerAvatar
                videoUrl={currentVideoUrl}
                audioUrl={currentAudioUrl}
                isFallbackMode={isFallbackMode}
                isGenerating={isGenerating}
                status="idle"
              />
            </div>
          ) : (
            <div className="comparison-grid">
              {comparePersonalities.slice(0, 3).map((personality) => (
                <div key={personality} className="comparison-item">
                  <h3>{personality}</h3>
                  <RafikiSadTalkerAvatar
                    videoUrl={personality === comparePersonalities[0] ? currentVideoUrl : undefined}
                    audioUrl={personality === comparePersonalities[0] ? currentAudioUrl : undefined}
                    isFallbackMode={isFallbackMode}
                    isGenerating={isGenerating && personality === comparePersonalities[0]}
                    status="idle"
                  />
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Info Section */}
        <section className="info-section">
          <h2>Understanding Personalities</h2>
          <div className="info-grid">
            <div className="info-card">
              <h4>Expression Scale</h4>
              <p>Controls the intensity of facial expressions. Higher values create more dramatic animations.</p>
            </div>
            <div className="info-card">
              <h4>Still Mode</h4>
              <p>When enabled, only the mouth moves (lip-sync). When disabled, the head moves naturally too.</p>
            </div>
            <div className="info-card">
              <h4>Preprocessing</h4>
              <p>Crop focuses on the face, Full includes more context for natural movements.</p>
            </div>
            <div className="info-card">
              <h4>Use Cases</h4>
              <p>Professional: formal announcements. Friendly: customer service. Excited: promotions. Calm: meditation/instructions.</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default PersonalityDemo;

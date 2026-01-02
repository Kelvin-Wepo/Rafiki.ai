/**
 * ElevenLabs Conversational AI Widget
 * Embeds the ElevenLabs talk-to page directly
 */

import React from 'react';

const AGENT_ID = 'agent_7901kbqbewwcf1avres326fjahdb';

function ElevenLabsWidget() {
  return (
    <div 
      className="elevenlabs-widget-container"
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '20px',
        width: '100%',
      }}
    >
      {/* Direct link to ElevenLabs Talk-To page */}
      <a
        href={`https://elevenlabs.io/app/talk-to?agent_id=${AGENT_ID}`}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '12px',
          padding: '16px 32px',
          backgroundColor: '#000000',
          color: '#ffffff',
          borderRadius: '50px',
          textDecoration: 'none',
          fontSize: '1.1rem',
          fontWeight: '600',
          transition: 'transform 0.2s, box-shadow 0.2s',
          boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25)',
        }}
        onMouseOver={(e) => {
          e.currentTarget.style.transform = 'scale(1.05)';
          e.currentTarget.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.35)';
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 4px 14px rgba(0, 0, 0, 0.25)';
        }}
      >
        <span style={{ fontSize: '1.5rem' }}>🎤</span>
        Talk to Habari
        <span style={{ fontSize: '0.8rem', opacity: 0.7 }}>↗</span>
      </a>
      
      <p style={{ 
        marginTop: '16px', 
        fontSize: '0.9rem', 
        color: '#666',
        textAlign: 'center',
      }}>
        Opens ElevenLabs voice assistant in a new tab
      </p>
    </div>
  );
}

export default ElevenLabsWidget;

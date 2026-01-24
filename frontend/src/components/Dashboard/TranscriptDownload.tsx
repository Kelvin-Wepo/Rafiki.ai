/**
 * Transcript Download Component
 * Allows users to download conversation transcripts in various formats.
 * 
 * Features:
 * - Format selection (TXT, JSON)
 * - Conversation selector
 * - Download progress
 */

import { useState, useEffect } from 'react';
import type { Conversation } from '../../services/authService';
import {
  getConversations,
  downloadTranscript,
} from '../../services/authService';
import './Dashboard.css';

interface TranscriptDownloadProps {
  preSelectedConversation?: Conversation | null;
}

type Format = 'txt' | 'json';

export function TranscriptDownload({ preSelectedConversation }: TranscriptDownloadProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<string>(
    preSelectedConversation?.id || ''
  );
  const [format, setFormat] = useState<Format>('txt');
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  /**
   * Fetch conversations for selector.
   */
  useEffect(() => {
    const fetchConversations = async () => {
      setIsLoading(true);
      try {
        const data = await getConversations();
        setConversations(data.conversations || []);
        
        // Auto-select first if no pre-selection
        if (!selectedId && data.conversations?.length > 0) {
          setSelectedId(data.conversations[0].id);
        }
      } catch {
        setError('Failed to load conversations');
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversations();
  }, [selectedId]);

  /**
   * Update selection when pre-selected changes.
   */
  useEffect(() => {
    if (preSelectedConversation?.id) {
      setSelectedId(preSelectedConversation.id);
    }
  }, [preSelectedConversation]);

  /**
   * Handle download.
   */
  const handleDownload = async () => {
    if (!selectedId) {
      setError('Please select a conversation');
      return;
    }

    setIsDownloading(true);
    setError(null);
    setSuccess(null);

    try {
      await downloadTranscript(selectedId, format);
      setSuccess(`Transcript downloaded successfully as ${format.toUpperCase()}`);
    } catch {
      setError('Failed to download transcript. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  /**
   * Format date for display.
   */
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-KE', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="loading-spinner">
        <div className="spinner-large" />
        <span>Loading...</span>
      </div>
    );
  }

  return (
    <div className="transcript-download">
      <div className="section-header">
        <div>
          <h2 className="section-title">Download Transcripts</h2>
          <p className="section-subtitle">
            Export your conversation history for record keeping
          </p>
        </div>
      </div>

      {conversations.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" />
            </svg>
          </div>
          <h3 className="empty-title">No transcripts available</h3>
          <p className="empty-description">
            Start a conversation to create transcripts for download
          </p>
        </div>
      ) : (
        <div className="transcript-section">
          {/* Conversation Selector */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label
              htmlFor="conversation-select"
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontWeight: 600,
                color: '#374151',
              }}
            >
              Select Conversation
            </label>
            <select
              id="conversation-select"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                border: '2px solid #e5e7eb',
                borderRadius: '10px',
                fontSize: '0.95rem',
                backgroundColor: '#ffffff',
                cursor: 'pointer',
              }}
            >
              {conversations.map((conv) => (
                <option key={conv.id} value={conv.id}>
                  {conv.title} - {formatDate(conv.created_at)}
                </option>
              ))}
            </select>
          </div>

          {/* Format Selection */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontWeight: 600,
                color: '#374151',
              }}
            >
              Export Format
            </label>
            <div className="transcript-options">
              <button
                type="button"
                className={`format-btn ${format === 'txt' ? 'format-btn-active' : ''}`}
                onClick={() => setFormat('txt')}
              >
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
                </svg>
                <span className="format-label">Plain Text (.txt)</span>
                <span className="format-desc">Simple readable format</span>
              </button>

              <button
                type="button"
                className={`format-btn ${format === 'json' ? 'format-btn-active' : ''}`}
                onClick={() => setFormat('json')}
              >
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z" />
                </svg>
                <span className="format-label">JSON (.json)</span>
                <span className="format-desc">Structured data format</span>
              </button>
            </div>
          </div>

          {/* Alerts */}
          {error && (
            <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
              <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 20, height: 20 }}>
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
              <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 20, height: 20 }}>
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
              </svg>
              <span>{success}</span>
            </div>
          )}

          {/* Download Button */}
          <button
            className="btn btn-primary btn-full"
            onClick={handleDownload}
            disabled={isDownloading || !selectedId}
            style={{ marginTop: '0.5rem' }}
          >
            {isDownloading ? (
              <>
                <span className="spinner" />
                Preparing download...
              </>
            ) : (
              <>
                <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 20, height: 20 }}>
                  <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" />
                </svg>
                Download Transcript
              </>
            )}
          </button>

          {/* Info */}
          <p
            style={{
              marginTop: '1rem',
              fontSize: '0.8rem',
              color: '#6b7280',
              textAlign: 'center',
            }}
          >
            <svg
              viewBox="0 0 24 24"
              fill="currentColor"
              style={{
                width: 14,
                height: 14,
                verticalAlign: 'middle',
                marginRight: '0.25rem',
              }}
            >
              <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
            </svg>
            Downloaded files are encrypted for your security
          </p>
        </div>
      )}
    </div>
  );
}

export default TranscriptDownload;

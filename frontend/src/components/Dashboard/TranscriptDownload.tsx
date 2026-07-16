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
import type { Conversation, ReceiptHistoryEntry } from '../../services/authService';
import useChatSessions from '../../hooks/useChatSessions';
import { downloadReceipt, getUserHistory } from '../../services/authService';
import { default as chatService } from '../../services/chatService';
import './Dashboard.css';

interface TranscriptDownloadProps {
  preSelectedConversation?: Conversation | null;
}

type Format = 'txt' | 'json' | 'pdf';

export function TranscriptDownload({ preSelectedConversation }: TranscriptDownloadProps) {
  const { sessions } = useChatSessions();
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<string>(
    preSelectedConversation?.id || ''
  );
  const [format, setFormat] = useState<Format>('txt');
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [receiptDownloadingId, setReceiptDownloadingId] = useState<string | null>(null);
  const [receipts, setReceipts] = useState<ReceiptHistoryEntry[]>([]);
  const [receiptError, setReceiptError] = useState<string | null>(null);
  const [receiptSuccess, setReceiptSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  /**
   * Fetch conversations for selector.
   */
  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true);
      try {
        // conversations from hook
        setConversations(sessions || []);
        const data = await getUserHistory();
        setReceipts(data.receipts || []);

        if (!selectedId && (sessions?.length || 0) > 0) {
          setSelectedId(sessions[0].id);
        }
      } catch (err) {
        setError('Failed to load conversations and receipts');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, []);

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
      setIsDownloading(true);
      const transcripts = await chatService.listTranscripts();
      // pick transcript for selected conversation
      const t = transcripts.find((x: any) => x.conversation_id === selectedId);
      if (!t) {
        // Ask backend to generate one
        await chatService.generateTranscript(selectedId, format);
        const refreshed = await chatService.listTranscripts();
        const t2 = refreshed.find((x: any) => x.conversation_id === selectedId);
        if (!t2) throw new Error('Transcript not available');
        const blob = await chatService.downloadTranscript(t2.transcript_id);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = t2.filename || `transcript_${selectedId}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const blob = await chatService.downloadTranscript(t.transcript_id);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = t.filename || `transcript_${selectedId}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
      setSuccess(`Transcript downloaded successfully as ${format.toUpperCase()}`);
    } catch (err) {
      console.error(err);
      setError('Failed to download transcript. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDownloadReceipt = async (receiptRef: string) => {
    setReceiptDownloadingId(receiptRef);
    setReceiptError(null);
    setReceiptSuccess(null);

    try {
      const blob = await downloadReceipt(receiptRef);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rafiki_receipt_${receiptRef}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setReceiptSuccess('Receipt downloaded successfully.');
    } catch {
      setReceiptError('Failed to download receipt. Please try again.');
    } finally {
      setReceiptDownloadingId(null);
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

      {conversations.length === 0 && receipts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" />
            </svg>
          </div>
          <h3 className="empty-title">No transcripts or receipts available</h3>
          <p className="empty-description">
            Start a conversation or complete a service payment to generate downloadable records.
          </p>
        </div>
      ) : (
        <div className="transcript-section">
          {conversations.length > 0 && (
            <>
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

                  <button
                    type="button"
                    className={`format-btn ${format === 'pdf' ? 'format-btn-active' : ''}`}
                    onClick={() => setFormat('pdf')}
                  >
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M6 2h9l5 5v15a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm9 1.5V8h4.5L15 3.5zM8 14h8v2H8v-2zm0-4h8v2H8v-2zm0-4h5v2H8V6z" />
                    </svg>
                    <span className="format-label">PDF (.pdf)</span>
                    <span className="format-desc">Printable document</span>
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
            </>
          )}

          {receipts.length > 0 ? (
            <div className="receipt-section" style={{ marginTop: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <h3 className="section-title">Receipt History</h3>
                  <p className="section-subtitle">
                    Download your verified service receipts as PDF documents.
                  </p>
                </div>
              </div>

              {receiptError && (
                <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
                  <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 20, height: 20 }}>
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
                  </svg>
                  <span>{receiptError}</span>
                </div>
              )}

              {receiptSuccess && (
                <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
                  <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 20, height: 20 }}>
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                  </svg>
                  <span>{receiptSuccess}</span>
                </div>
              )}

              <div className="receipt-list" style={{ display: 'grid', gap: '1rem' }}>
                {receipts.map((receipt) => (
                  <div key={receipt.receipt_ref} className="receipt-card" style={{ padding: '1rem', border: '1px solid #e5e7eb', borderRadius: '16px', background: '#ffffff' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'flex-start' }}>
                      <div>
                        <p style={{ margin: 0, fontWeight: 700, color: '#111827' }}>{receipt.service}</p>
                        <p style={{ margin: '0.25rem 0 0', color: '#6b7280', fontSize: '0.9rem' }}>{receipt.agency}</p>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <p style={{ margin: 0, fontWeight: 700, color: '#111827' }}>KES {receipt.amount?.toLocaleString() ?? 'N/A'}</p>
                        <p style={{ margin: '0.25rem 0 0', color: receipt.status === 'paid' ? '#16a34a' : '#d97706', fontSize: '0.85rem' }}>{receipt.status?.toUpperCase()}</p>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gap: '0.5rem', marginTop: '1rem', color: '#4b5563', fontSize: '0.9rem' }}>
                      <p style={{ margin: 0 }}>Ref: {receipt.payment_reference || receipt.receipt_ref}</p>
                      <p style={{ margin: 0 }}>Date: {formatDate(receipt.created_at)}</p>
                      <p style={{ margin: 0 }}>Name: {receipt.name || 'Unknown'}</p>
                      <p style={{ margin: 0 }}>Phone: {receipt.phone || 'Unknown'}</p>
                      {receipt.appointment?.date && (
                        <p style={{ margin: 0 }}>Appointment: {receipt.appointment.date} at {receipt.appointment.time}</p>
                      )}
                    </div>

                    <button
                      className="btn btn-secondary btn-full"
                      onClick={() => handleDownloadReceipt(receipt.receipt_ref)}
                      disabled={receiptDownloadingId === receipt.receipt_ref}
                      style={{ marginTop: '1rem' }}
                    >
                      {receiptDownloadingId === receipt.receipt_ref ? 'Downloading receipt...' : 'Download Receipt PDF'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty-state" style={{ marginTop: '2rem' }}>
              <h3 className="empty-title">No receipts yet</h3>
              <p className="empty-description">
                Your paid services and receipts will appear here once completed.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default TranscriptDownload;

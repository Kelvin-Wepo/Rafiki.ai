import { useState } from 'react';
import './CheckWaitlistStatus.css';

interface StatusResponse {
  success: boolean;
  phone_number: string;
  status: 'pending' | 'activated' | 'cancelled';
  position?: number;
  message: string;
  joined_at?: string;
  activated_at?: string;
  error?: string;
}

export function CheckWaitlistStatus() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCheck = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setStatus(null);

    try {
      const response = await fetch(
        `http://localhost:8000/waitlist/status?phone_number=${encodeURIComponent(phoneNumber)}`
      );

      const data: StatusResponse = await response.json();

      if (response.ok && data.success) {
        setStatus(data);
      } else {
        setError(data.error || data.message || 'Could not find phone number');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'activated':
        return 'status-activated';
      case 'pending':
        return 'status-pending';
      case 'cancelled':
        return 'status-cancelled';
      default:
        return '';
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'activated':
        return '✓';
      case 'pending':
        return '⏳';
      case 'cancelled':
        return '✕';
      default:
        return '?';
    }
  };

  return (
    <div className="status-container">
      <div className="status-card">
        <div className="status-header">
          <h2>Check Your Waitlist Status</h2>
          <p>Enter your phone number to see your position</p>
        </div>

        <form onSubmit={handleCheck} className="status-form">
          <div className="form-group">
            <label htmlFor="phone">Phone Number</label>
            <input
              type="tel"
              id="phone"
              placeholder="0712345678"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              required
            />
          </div>

          {error && (
            <div className="error-message">
              <span>⚠ {error}</span>
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-check">
            {loading ? (
              <>
                <span className="spinner"></span>
                Checking...
              </>
            ) : (
              'Check Status'
            )}
          </button>
        </form>

        {status && (
          <div className={`status-result ${getStatusColor(status.status)}`}>
            <div className="status-icon">{getStatusIcon(status.status)}</div>
            <div className="status-content">
              <h3>
                {status.status === 'activated'
                  ? 'Account Activated! 🎉'
                  : status.status === 'pending'
                  ? 'You are on the Waitlist'
                  : 'Status: Cancelled'}
              </h3>
              
              {status.status === 'pending' && status.position && (
                <p className="position-info">
                  Position: <span className="position">#{status.position}</span>
                </p>
              )}
              
              <p className="message">{status.message}</p>

              {status.joined_at && (
                <p className="date-info">
                  Joined: {new Date(status.joined_at).toLocaleDateString()}
                </p>
              )}

              {status.activated_at && (
                <p className="date-info">
                  Activated: {new Date(status.activated_at).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

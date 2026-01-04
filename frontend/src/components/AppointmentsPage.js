import React, { useState, useEffect } from 'react';
import { useSession } from '../context/SessionContext';
import { useAccessibility } from '../context/AccessibilityContext';
import { bookingAPI } from '../services/api';

const AppointmentsPage = () => {
  const { sessionId } = useSession();
  const { speak } = useAccessibility();
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [cancellingId, setCancellingId] = useState(null);

  useEffect(() => {
    fetchAppointments();
  }, [sessionId]);

  useEffect(() => {
    if (!loading && appointments.length > 0) {
      speak(`You have ${appointments.length} appointments. Use arrow keys to navigate through them.`);
    } else if (!loading && appointments.length === 0) {
      speak('You have no appointments scheduled.');
    }
  }, [loading, appointments.length, speak]);

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      const response = await bookingAPI.getUserBookings(sessionId);
      setAppointments(response.data.bookings || []);
    } catch (err) {
      setError('Failed to load appointments. Please try again.');
      console.error('Error fetching appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelAppointment = async (appointmentId) => {
    const confirmed = window.confirm(
      'Are you sure you want to cancel this appointment? You will need to book a new one.'
    );
    
    if (!confirmed) return;

    try {
      setCancellingId(appointmentId);
      await bookingAPI.cancelBooking(appointmentId);
      setAppointments(prev => 
        prev.map(apt => 
          apt.id === appointmentId 
            ? { ...apt, status: 'cancelled' }
            : apt
        )
      );
      speak('Appointment cancelled successfully.');
    } catch (err) {
      setError('Failed to cancel appointment. Please try again.');
      speak('Failed to cancel appointment.');
    } finally {
      setCancellingId(null);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'confirmed': return '#006600';
      case 'pending': return '#cc7a00';
      case 'cancelled': return '#cc0000';
      case 'completed': return '#0066cc';
      default: return '#666666';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'confirmed': return '✓';
      case 'pending': return '⏳';
      case 'cancelled': return '✗';
      case 'completed': return '✓✓';
      default: return '?';
    }
  };

  const filteredAppointments = appointments.filter(apt => {
    if (filter === 'all') return true;
    return apt.status === filter;
  });

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-KE', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatTime = (timeString) => {
    return timeString;
  };

  const isUpcoming = (dateString) => {
    return new Date(dateString) > new Date();
  };

  if (loading) {
    return (
      <main className="appointments-page" role="main">
        <div className="loading-container">
          <div className="loading-spinner" aria-hidden="true"></div>
          <p role="status" aria-live="polite">Loading your appointments...</p>
        </div>
        <style jsx>{`
          .appointments-page {
            padding: 2rem;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .loading-container {
            text-align: center;
          }
          .loading-spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #eee;
            border-top-color: #006600;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
          }
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </main>
    );
  }

  return (
    <main 
      className="appointments-page"
      role="main"
      aria-labelledby="appointments-title"
    >
      <div className="container">
        <header className="page-header">
          <h1 id="appointments-title" tabIndex="-1">
            My Appointments
          </h1>
          <p className="page-description">
            View and manage your scheduled appointments
          </p>
        </header>

        {error && (
          <div 
            className="error-message"
            role="alert"
            aria-live="assertive"
          >
            <span className="error-icon" aria-hidden="true">⚠️</span>
            {error}
            <button 
              onClick={() => setError(null)}
              className="dismiss-btn"
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        )}

        <div className="filters" role="group" aria-label="Filter appointments">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
            aria-pressed={filter === 'all'}
          >
            All ({appointments.length})
          </button>
          <button
            className={`filter-btn ${filter === 'confirmed' ? 'active' : ''}`}
            onClick={() => setFilter('confirmed')}
            aria-pressed={filter === 'confirmed'}
          >
            Confirmed
          </button>
          <button
            className={`filter-btn ${filter === 'pending' ? 'active' : ''}`}
            onClick={() => setFilter('pending')}
            aria-pressed={filter === 'pending'}
          >
            Pending
          </button>
          <button
            className={`filter-btn ${filter === 'cancelled' ? 'active' : ''}`}
            onClick={() => setFilter('cancelled')}
            aria-pressed={filter === 'cancelled'}
          >
            Cancelled
          </button>
        </div>

        {filteredAppointments.length === 0 ? (
          <div className="empty-state" role="status">
            <span className="empty-icon" aria-hidden="true">📅</span>
            <h2>No appointments found</h2>
            <p>
              {filter === 'all' 
                ? "You haven't booked any appointments yet."
                : `No ${filter} appointments found.`}
            </p>
            <a 
              href="/services" 
              className="btn btn-primary"
              aria-label="Go to services page to book an appointment"
            >
              Book an Appointment
            </a>
          </div>
        ) : (
          <div className="appointments-list" role="list">
            {filteredAppointments.map((appointment, index) => (
              <article
                key={appointment.id}
                className={`appointment-card ${appointment.status}`}
                role="listitem"
                aria-labelledby={`apt-title-${appointment.id}`}
                tabIndex="0"
              >
                <div className="appointment-header">
                  <div 
                    className="status-badge"
                    style={{ backgroundColor: getStatusColor(appointment.status) }}
                    role="status"
                  >
                    <span aria-hidden="true">{getStatusIcon(appointment.status)}</span>
                    {appointment.status}
                  </div>
                  {isUpcoming(appointment.date) && appointment.status === 'confirmed' && (
                    <span className="upcoming-badge">Upcoming</span>
                  )}
                </div>

                <h2 id={`apt-title-${appointment.id}`} className="service-name">
                  {appointment.service_name || appointment.service}
                </h2>

                <div className="appointment-details">
                  <div className="detail-row">
                    <span className="detail-icon" aria-hidden="true">📅</span>
                    <span className="detail-label">Date:</span>
                    <span className="detail-value">{formatDate(appointment.date)}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-icon" aria-hidden="true">🕐</span>
                    <span className="detail-label">Time:</span>
                    <span className="detail-value">{formatTime(appointment.time)}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-icon" aria-hidden="true">📍</span>
                    <span className="detail-label">Location:</span>
                    <span className="detail-value">{appointment.location || 'Huduma Centre, Nairobi'}</span>
                  </div>
                  {appointment.reference_number && (
                    <div className="detail-row">
                      <span className="detail-icon" aria-hidden="true">🔢</span>
                      <span className="detail-label">Reference:</span>
                      <span className="detail-value reference">{appointment.reference_number}</span>
                    </div>
                  )}
                </div>

                {appointment.status === 'confirmed' && isUpcoming(appointment.date) && (
                  <div className="appointment-actions">
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleCancelAppointment(appointment.id)}
                      disabled={cancellingId === appointment.id}
                      aria-label={`Cancel appointment for ${appointment.service_name}`}
                    >
                      {cancellingId === appointment.id ? 'Cancelling...' : 'Cancel Appointment'}
                    </button>
                    <button
                      className="btn btn-outline"
                      onClick={() => speak(`Your appointment for ${appointment.service_name} is on ${formatDate(appointment.date)} at ${formatTime(appointment.time)}`)}
                      aria-label="Hear appointment details"
                    >
                      🔊 Read Aloud
                    </button>
                  </div>
                )}

                {appointment.status === 'cancelled' && (
                  <div className="cancelled-notice">
                    <p>This appointment has been cancelled.</p>
                    <a 
                      href="/booking" 
                      className="btn btn-primary"
                      aria-label="Book a new appointment"
                    >
                      Book New Appointment
                    </a>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}

        <section className="help-section" aria-labelledby="help-title">
          <h2 id="help-title">Need Help?</h2>
          <p>
            If you need to reschedule or have questions about your appointment, 
            please contact the Huduma Centre or use the voice assistant.
          </p>
          <div className="help-actions">
            <a href="/help" className="btn btn-outline">
              View Help Guide
            </a>
            <a href="tel:0800723400" className="btn btn-outline">
              📞 Call Support
            </a>
          </div>
        </section>
      </div>

      <style jsx>{`
        .appointments-page {
          padding: 2rem 1rem;
          min-height: 100vh;
        }

        .container {
          max-width: 900px;
          margin: 0 auto;
        }

        .page-header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .page-header h1 {
          font-size: 2.5rem;
          margin-bottom: 0.5rem;
        }

        .page-description {
          font-size: 1.125rem;
          opacity: 0.8;
        }

        .error-message {
          background: #fee;
          border: 1px solid #fcc;
          color: #c00;
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 1.5rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .dismiss-btn {
          margin-left: auto;
          background: none;
          border: none;
          font-size: 1.25rem;
          cursor: pointer;
          padding: 0.25rem 0.5rem;
        }

        .filters {
          display: flex;
          gap: 0.75rem;
          margin-bottom: 2rem;
          flex-wrap: wrap;
        }

        .filter-btn {
          padding: 0.75rem 1.5rem;
          border: 2px solid var(--primary-color, #006600);
          background: transparent;
          color: var(--primary-color, #006600);
          border-radius: 25px;
          font-size: 1rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .filter-btn:hover,
        .filter-btn.active {
          background: var(--primary-color, #006600);
          color: white;
        }

        .empty-state {
          text-align: center;
          padding: 4rem 2rem;
          background: var(--card-bg, white);
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .empty-icon {
          font-size: 4rem;
          display: block;
          margin-bottom: 1rem;
        }

        .empty-state h2 {
          margin-bottom: 0.5rem;
        }

        .empty-state p {
          margin-bottom: 1.5rem;
          opacity: 0.8;
        }

        .appointments-list {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .appointment-card {
          background: var(--card-bg, white);
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          border-left: 4px solid var(--primary-color, #006600);
        }

        .appointment-card.cancelled {
          border-left-color: #cc0000;
          opacity: 0.7;
        }

        .appointment-card.pending {
          border-left-color: #cc7a00;
        }

        .appointment-header {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 1rem;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.25rem 0.75rem;
          border-radius: 15px;
          color: white;
          font-size: 0.875rem;
          font-weight: 600;
          text-transform: capitalize;
        }

        .upcoming-badge {
          background: #e6f3ff;
          color: #0066cc;
          padding: 0.25rem 0.75rem;
          border-radius: 15px;
          font-size: 0.75rem;
          font-weight: 600;
        }

        .service-name {
          font-size: 1.5rem;
          margin-bottom: 1rem;
          color: var(--text-color, #333);
        }

        .appointment-details {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          margin-bottom: 1.5rem;
        }

        .detail-row {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .detail-icon {
          font-size: 1.25rem;
        }

        .detail-label {
          font-weight: 600;
          min-width: 80px;
        }

        .detail-value {
          color: var(--text-color, #333);
        }

        .detail-value.reference {
          font-family: monospace;
          background: var(--hover-bg, #f5f5f5);
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
        }

        .appointment-actions {
          display: flex;
          gap: 1rem;
          flex-wrap: wrap;
        }

        .btn {
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          font-size: 1rem;
          cursor: pointer;
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          transition: all 0.2s;
        }

        .btn-primary {
          background: var(--primary-color, #006600);
          color: white;
          border: none;
        }

        .btn-primary:hover {
          background: var(--primary-dark, #004d00);
        }

        .btn-secondary {
          background: #cc0000;
          color: white;
          border: none;
        }

        .btn-secondary:hover {
          background: #990000;
        }

        .btn-secondary:disabled {
          background: #999;
          cursor: not-allowed;
        }

        .btn-outline {
          background: transparent;
          border: 2px solid var(--primary-color, #006600);
          color: var(--primary-color, #006600);
        }

        .btn-outline:hover {
          background: var(--primary-color, #006600);
          color: white;
        }

        .cancelled-notice {
          background: #fee;
          padding: 1rem;
          border-radius: 8px;
          text-align: center;
        }

        .cancelled-notice p {
          margin-bottom: 1rem;
          color: #c00;
        }

        .help-section {
          margin-top: 3rem;
          padding: 2rem;
          background: var(--card-bg, white);
          border-radius: 12px;
          text-align: center;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .help-section h2 {
          margin-bottom: 0.5rem;
        }

        .help-section p {
          margin-bottom: 1.5rem;
          opacity: 0.8;
        }

        .help-actions {
          display: flex;
          gap: 1rem;
          justify-content: center;
          flex-wrap: wrap;
        }

        @media (max-width: 768px) {
          .page-header h1 {
            font-size: 1.75rem;
          }

          .filters {
            justify-content: center;
          }

          .filter-btn {
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
          }

          .appointment-actions {
            flex-direction: column;
          }

          .btn {
            width: 100%;
            justify-content: center;
          }
        }
      `}</style>
    </main>
  );
};

export default AppointmentsPage;

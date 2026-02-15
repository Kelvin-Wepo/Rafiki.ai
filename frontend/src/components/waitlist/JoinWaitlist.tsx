import { useState } from 'react';
import './JoinWaitlist.css';

interface WaitlistFormData {
  phone_number: string;
  email: string;
  full_name: string;
  service_interest: 'general' | 'passport' | 'national_id' | 'driving_license' | 'good_conduct' | 'kra_services' | 'ecitizen_services';
}

interface WaitlistResponse {
  success: boolean;
  message: string;
  position?: number;
  id?: string;
  joined_at?: string;
  error?: string;
}

export function JoinWaitlist() {
  const [formData, setFormData] = useState<WaitlistFormData>({
    phone_number: '',
    email: '',
    full_name: '',
    service_interest: 'general'
  });

  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [response, setResponse] = useState<WaitlistResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/waitlist/join', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data: WaitlistResponse = await response.json();

      if (response.ok && data.success) {
        setResponse(data);
        setSubmitted(true);
        setFormData({
          phone_number: '',
          email: '',
          full_name: '',
          service_interest: 'general'
        });
      } else {
        setError(data.error || data.message || 'Failed to join waitlist');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="waitlist-container">
      <div className="waitlist-card">
        <div className="waitlist-header">
          <h2>Join Our Waitlist</h2>
          <p>Get early access to new Rafiki features and government services</p>
        </div>

        {submitted && response?.success ? (
          <div className="success-message">
            <div className="success-icon">✓</div>
            <h3>Welcome to the Waitlist!</h3>
            <p className="position-text">
              You're <span className="position-number">#{response.position}</span> in line
            </p>
            <p className="message-text">{response.message}</p>
            <p className="confirmation-text">
              We'll send you an SMS when it's your turn. Thank you for your patience!
            </p>
            <button 
              onClick={() => setSubmitted(false)}
              className="btn-again"
            >
              ← Back to Form
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="waitlist-form">
            <div className="form-group">
              <label htmlFor="phone_number">Phone Number *</label>
              <input
                type="tel"
                id="phone_number"
                name="phone_number"
                placeholder="0712345678 or +254712345678"
                value={formData.phone_number}
                onChange={handleChange}
                required
              />
              <small>Kenyan phone number (starts with 07 or 01)</small>
            </div>

            <div className="form-group">
              <label htmlFor="full_name">Full Name</label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                placeholder="Your full name"
                value={formData.full_name}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                name="email"
                placeholder="your@email.com"
                value={formData.email}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="service_interest">Service Interest</label>
              <select
                id="service_interest"
                name="service_interest"
                value={formData.service_interest}
                onChange={handleChange}
              >
                <option value="general">General Interest</option>
                <option value="passport">Passport Application</option>
                <option value="national_id">National ID</option>
                <option value="driving_license">Driving License</option>
                <option value="good_conduct">Certificate of Good Conduct</option>
                <option value="kra_services">KRA Services</option>
                <option value="ecitizen_services">eCitizen Services</option>
              </select>
            </div>

            {error && (
              <div className="error-message">
                <span>⚠ {error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-submit"
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Joining...
                </>
              ) : (
                'Join Waitlist'
              )}
            </button>

            <p className="terms-text">
              We respect your privacy. Your information will only be used to notify you about your position on the waitlist.
            </p>
          </form>
        )}
      </div>
    </div>
  );
}

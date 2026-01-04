/**
 * Booking Page Component
 * Multi-step booking form with full accessibility
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAccessibility } from '../context/AccessibilityContext';
import { useSession } from '../context/SessionContext';
import ProgressSteps from './ProgressSteps';
import TimeSlotPicker from './TimeSlotPicker';
import ServiceCard from './ServiceCard';
import api from '../services/api';
import toast from 'react-hot-toast';
import { format, addDays } from 'date-fns';

const bookingSteps = [
  { label: 'Service' },
  { label: 'Details' },
  { label: 'Time' },
  { label: 'Confirm' },
];

function BookingPage() {
  const { serviceType } = useParams();
  const navigate = useNavigate();
  const { announce, speak, settings } = useAccessibility();
  const { sessionId, updateBookingState, bookingState } = useSession();

  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [services, setServices] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [bookingConfirmation, setBookingConfirmation] = useState(null);
  
  const [formData, setFormData] = useState({
    serviceType: serviceType || '',
    userName: '',
    phoneNumber: '',
    timeSlot: '',
    appointmentDate: format(addDays(new Date(), 1), 'yyyy-MM-dd'),
    additionalNotes: '',
  });

  const [errors, setErrors] = useState({});

  // Load services on mount
  useEffect(() => {
    loadServices();
  }, []);

  // Set service from URL param
  useEffect(() => {
    if (serviceType && services.length > 0) {
      const service = services.find(s => s.service_type === serviceType);
      if (service) {
        setSelectedService(service);
        setFormData(prev => ({ ...prev, serviceType }));
        setCurrentStep(1);
        announce(`Selected ${service.name}. Please enter your details.`);
      }
    }
  }, [serviceType, services, announce]);

  const loadServices = async () => {
    try {
      const data = await api.getServices();
      setServices(data.services || []);
    } catch (error) {
      console.error('Failed to load services:', error);
      toast.error('Failed to load services');
    }
  };

  const validateStep = (step) => {
    const newErrors = {};

    switch (step) {
      case 0:
        if (!formData.serviceType) {
          newErrors.serviceType = 'Please select a service';
        }
        break;
      case 1:
        if (!formData.userName.trim()) {
          newErrors.userName = 'Please enter your full name';
        } else if (formData.userName.length < 2) {
          newErrors.userName = 'Name must be at least 2 characters';
        }
        
        if (!formData.phoneNumber.trim()) {
          newErrors.phoneNumber = 'Please enter your phone number';
        } else if (!/^(\+254|254|0)?[17]\d{8}$/.test(formData.phoneNumber.replace(/[\s-]/g, ''))) {
          newErrors.phoneNumber = 'Please enter a valid Kenyan phone number';
        }
        break;
      case 2:
        if (!formData.timeSlot) {
          newErrors.timeSlot = 'Please select a time slot';
        }
        if (!formData.appointmentDate) {
          newErrors.appointmentDate = 'Please select a date';
        } else {
          const selectedDate = new Date(formData.appointmentDate);
          const today = new Date();
          today.setHours(0, 0, 0, 0);
          if (selectedDate < today) {
            newErrors.appointmentDate = 'Please select a future date';
          }
        }
        break;
      default:
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      if (currentStep < bookingSteps.length - 1) {
        setCurrentStep(prev => prev + 1);
        announce(`Step ${currentStep + 2}: ${bookingSteps[currentStep + 1].label}`);
      }
    } else {
      const errorMessages = Object.values(errors).join('. ');
      announce(`Please fix the following errors: ${errorMessages}`);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
      announce(`Step ${currentStep}: ${bookingSteps[currentStep - 1].label}`);
    }
  };

  const handleServiceSelect = (service) => {
    setSelectedService(service);
    setFormData(prev => ({ ...prev, serviceType: service.service_type }));
    handleNext();
    
    if (settings.voiceEnabled) {
      speak(`You selected ${service.name}. Now please enter your details.`);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleTimeSlotSelect = (slot) => {
    setFormData(prev => ({ ...prev, timeSlot: slot }));
    if (errors.timeSlot) {
      setErrors(prev => ({ ...prev, timeSlot: '' }));
    }
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setIsLoading(true);
    announce('Processing your booking...');

    try {
      // Normalize phone number
      let phone = formData.phoneNumber.replace(/[\s-]/g, '');
      if (phone.startsWith('0')) {
        phone = '+254' + phone.slice(1);
      } else if (phone.startsWith('254')) {
        phone = '+' + phone;
      } else if (!phone.startsWith('+')) {
        phone = '+254' + phone;
      }

      const response = await api.createBooking({
        service_type: formData.serviceType,
        user_name: formData.userName,
        phone_number: phone,
        time_slot: formData.timeSlot,
        appointment_date: new Date(formData.appointmentDate).toISOString(),
        session_id: sessionId,
        additional_notes: formData.additionalNotes || null,
      });

      if (response.success) {
        setBookingConfirmation(response);
        toast.success('Booking confirmed!');
        
        const confirmationMessage = `Your booking is confirmed! 
          Booking ID: ${response.booking_id}. 
          ${response.sms_sent ? 'An SMS confirmation has been sent to your phone.' : ''}`;
        
        announce(confirmationMessage);
        if (settings.voiceEnabled) {
          speak(confirmationMessage);
        }
      } else {
        throw new Error(response.message || 'Booking failed');
      }
    } catch (error) {
      console.error('Booking error:', error);
      toast.error(error.message || 'Failed to create booking');
      announce('Booking failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getMinDate = () => {
    const tomorrow = addDays(new Date(), 1);
    return format(tomorrow, 'yyyy-MM-dd');
  };

  const getMaxDate = () => {
    const maxDate = addDays(new Date(), 90);
    return format(maxDate, 'yyyy-MM-dd');
  };

  // Render booking confirmation
  if (bookingConfirmation) {
    const booking = bookingConfirmation.booking_details;
    
    return (
      <div className="container">
        <div className="booking-container">
          <div className="confirmation-card">
            <div className="confirmation-header">
              <svg 
                className="confirmation-icon" 
                viewBox="0 0 24 24" 
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
              <h1 className="confirmation-title">Booking Confirmed!</h1>
            </div>
            
            <div className="confirmation-body">
              <div className="confirmation-details">
                <div className="confirmation-detail">
                  <span className="confirmation-detail-label">Booking ID</span>
                  <span className="confirmation-detail-value">{booking?.booking_id}</span>
                </div>
                <div className="confirmation-detail">
                  <span className="confirmation-detail-label">Service</span>
                  <span className="confirmation-detail-value">{booking?.service_name}</span>
                </div>
                <div className="confirmation-detail">
                  <span className="confirmation-detail-label">Name</span>
                  <span className="confirmation-detail-value">{booking?.user_name}</span>
                </div>
                <div className="confirmation-detail">
                  <span className="confirmation-detail-label">Date</span>
                  <span className="confirmation-detail-value">
                    {booking?.appointment_date && format(new Date(booking.appointment_date), 'MMMM d, yyyy')}
                  </span>
                </div>
                <div className="confirmation-detail">
                  <span className="confirmation-detail-label">Time</span>
                  <span className="confirmation-detail-value">{booking?.time_slot}</span>
                </div>
                <div className="confirmation-detail">
                  <span className="confirmation-detail-label">Department</span>
                  <span className="confirmation-detail-value">{booking?.department}</span>
                </div>
              </div>

              {bookingConfirmation.sms_sent && (
                <div className="confirmation-sms">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/>
                  </svg>
                  <span>SMS confirmation sent to {booking?.phone_number}</span>
                </div>
              )}

              <div style={{ marginTop: 'var(--spacing-xl)' }}>
                <h3 style={{ marginBottom: 'var(--spacing-sm)' }}>Required Documents</h3>
                <ul style={{ paddingLeft: 'var(--spacing-lg)' }}>
                  {booking?.requirements?.map((req, index) => (
                    <li key={index}>{req}</li>
                  ))}
                </ul>
              </div>

              <div style={{ display: 'flex', gap: 'var(--spacing-md)', marginTop: 'var(--spacing-xl)' }}>
                <button
                  className="btn btn-secondary"
                  onClick={() => navigate('/services')}
                  style={{ flex: 1 }}
                >
                  Back to Services
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => navigate('/')}
                  style={{ flex: 1 }}
                >
                  Home
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="booking-container">
        <div className="booking-header">
          <h1>Book an Appointment</h1>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            Complete the steps below to book your appointment
          </p>
        </div>

        <ProgressSteps
          steps={bookingSteps}
          currentStep={currentStep}
          onStepClick={(step) => step < currentStep && setCurrentStep(step)}
        />

        <div className="booking-form">
          {/* Step 1: Select Service */}
          {currentStep === 0 && (
            <div role="group" aria-labelledby="step-service-title">
              <h2 id="step-service-title" style={{ marginBottom: 'var(--spacing-lg)' }}>
                Select a Service
              </h2>
              
              <div className="services-grid">
                {services.map((service) => (
                  <ServiceCard
                    key={service.service_type}
                    service={service}
                    onSelect={handleServiceSelect}
                  />
                ))}
              </div>
              
              {errors.serviceType && (
                <p className="form-error" role="alert">{errors.serviceType}</p>
              )}
            </div>
          )}

          {/* Step 2: Enter Details */}
          {currentStep === 1 && (
            <div role="group" aria-labelledby="step-details-title">
              <h2 id="step-details-title" style={{ marginBottom: 'var(--spacing-lg)' }}>
                Your Details
              </h2>
              
              {selectedService && (
                <div 
                  style={{ 
                    padding: 'var(--spacing-md)', 
                    backgroundColor: 'var(--color-bg-secondary)',
                    borderRadius: 'var(--radius-md)',
                    marginBottom: 'var(--spacing-lg)'
                  }}
                >
                  <strong>Selected Service:</strong> {selectedService.name}
                </div>
              )}
              
              <div className="form-group">
                <label htmlFor="userName" className="form-label">
                  Full Name *
                </label>
                <input
                  type="text"
                  id="userName"
                  name="userName"
                  className="form-input"
                  value={formData.userName}
                  onChange={handleInputChange}
                  placeholder="Enter your full name"
                  aria-required="true"
                  aria-invalid={!!errors.userName}
                  aria-describedby={errors.userName ? 'userName-error' : undefined}
                />
                {errors.userName && (
                  <p id="userName-error" className="form-error" role="alert">
                    {errors.userName}
                  </p>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="phoneNumber" className="form-label">
                  Phone Number *
                </label>
                <input
                  type="tel"
                  id="phoneNumber"
                  name="phoneNumber"
                  className="form-input"
                  value={formData.phoneNumber}
                  onChange={handleInputChange}
                  placeholder="e.g., 0712345678"
                  aria-required="true"
                  aria-invalid={!!errors.phoneNumber}
                  aria-describedby="phone-help phoneNumber-error"
                />
                <p id="phone-help" className="form-help">
                  Enter your Kenyan phone number for SMS confirmation
                </p>
                {errors.phoneNumber && (
                  <p id="phoneNumber-error" className="form-error" role="alert">
                    {errors.phoneNumber}
                  </p>
                )}
              </div>

              <div className="booking-actions">
                <button
                  className="btn btn-secondary"
                  onClick={handleBack}
                >
                  Back
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleNext}
                >
                  Continue
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Select Time */}
          {currentStep === 2 && (
            <div role="group" aria-labelledby="step-time-title">
              <h2 id="step-time-title" style={{ marginBottom: 'var(--spacing-lg)' }}>
                Select Date & Time
              </h2>

              <div className="form-group">
                <label htmlFor="appointmentDate" className="form-label">
                  Appointment Date *
                </label>
                <input
                  type="date"
                  id="appointmentDate"
                  name="appointmentDate"
                  className="form-input"
                  value={formData.appointmentDate}
                  onChange={handleInputChange}
                  min={getMinDate()}
                  max={getMaxDate()}
                  aria-required="true"
                  aria-invalid={!!errors.appointmentDate}
                />
                {errors.appointmentDate && (
                  <p className="form-error" role="alert">{errors.appointmentDate}</p>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">Time Slot *</label>
                <TimeSlotPicker
                  selectedSlot={formData.timeSlot}
                  onSelect={handleTimeSlotSelect}
                />
                {errors.timeSlot && (
                  <p className="form-error" role="alert">{errors.timeSlot}</p>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="additionalNotes" className="form-label">
                  Additional Notes (Optional)
                </label>
                <textarea
                  id="additionalNotes"
                  name="additionalNotes"
                  className="form-input form-textarea"
                  value={formData.additionalNotes}
                  onChange={handleInputChange}
                  placeholder="Any special requirements or notes"
                  rows={3}
                />
              </div>

              <div className="booking-actions">
                <button
                  className="btn btn-secondary"
                  onClick={handleBack}
                >
                  Back
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleNext}
                >
                  Review Booking
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Confirm */}
          {currentStep === 3 && (
            <div role="group" aria-labelledby="step-confirm-title">
              <h2 id="step-confirm-title" style={{ marginBottom: 'var(--spacing-lg)' }}>
                Confirm Your Booking
              </h2>

              <div className="confirmation-details" style={{ marginBottom: 'var(--spacing-xl)' }}>
                <div className="confirmation-detail">
                  <span className="confirmation-detail-label">Service</span>
                  <span className="confirmation-detail-value">{selectedService?.name}</span>
                </div>
                <div className="confirmation-detail">
                  <span className="confirmation-detail-label">Name</span>
                  <span className="confirmation-detail-value">{formData.userName}</span>
                </div>
                <div className="confirmation-detail">
                  <span className="confirmation-detail-label">Phone</span>
                  <span className="confirmation-detail-value">{formData.phoneNumber}</span>
                </div>
                <div className="confirmation-detail">
                  <span className="confirmation-detail-label">Date</span>
                  <span className="confirmation-detail-value">
                    {format(new Date(formData.appointmentDate), 'MMMM d, yyyy')}
                  </span>
                </div>
                <div className="confirmation-detail">
                  <span className="confirmation-detail-label">Time</span>
                  <span className="confirmation-detail-value">
                    {formData.timeSlot === '08:00-12:00' ? 'Morning (8 AM - 12 PM)' : 'Afternoon (2 PM - 5 PM)'}
                  </span>
                </div>
                {formData.additionalNotes && (
                  <div className="confirmation-detail">
                    <span className="confirmation-detail-label">Notes</span>
                    <span className="confirmation-detail-value">{formData.additionalNotes}</span>
                  </div>
                )}
              </div>

              <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-lg)' }}>
                You will receive an SMS confirmation to {formData.phoneNumber}
              </p>

              <div className="booking-actions">
                <button
                  className="btn btn-secondary"
                  onClick={handleBack}
                  disabled={isLoading}
                >
                  Back
                </button>
                <button
                  className="btn btn-success btn-large"
                  onClick={handleSubmit}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <span className="loading-spinner" aria-hidden="true" />
                      Processing...
                    </>
                  ) : (
                    'Confirm Booking'
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default BookingPage;

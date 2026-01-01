/**
 * Services Page Component
 * Display all available government services
 */

import React, { useEffect, useState } from 'react';
import { useAccessibility } from '../context/AccessibilityContext';
import ServiceCard from './ServiceCard';
import api from '../services/api';
import toast from 'react-hot-toast';

function ServicesPage() {
  const [services, setServices] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const { announce, speak, settings } = useAccessibility();

  useEffect(() => {
    loadServices();
    announce('Services page loaded');
  }, [announce]);

  const loadServices = async () => {
    setIsLoading(true);
    try {
      const data = await api.getServices();
      setServices(data.services || []);
    } catch (error) {
      console.error('Failed to load services:', error);
      toast.error('Failed to load services');
    } finally {
      setIsLoading(false);
    }
  };

  const handleServiceSelect = async (service) => {
    setSelectedService(service);
    
    // Load requirements
    try {
      const requirements = await api.getServiceRequirements(service.service_type);
      setSelectedService(prev => ({ ...prev, ...requirements }));
      
      if (settings.voiceEnabled) {
        speak(requirements.requirements_text);
      }
    } catch (error) {
      console.error('Failed to load requirements:', error);
    }
  };

  const handleCloseDetails = () => {
    setSelectedService(null);
    announce('Service details closed');
  };

  if (isLoading) {
    return (
      <div className="container">
        <div className="loading-overlay" style={{ position: 'relative', minHeight: '400px' }}>
          <div className="loading-content">
            <span className="loading-spinner" />
            <p className="loading-text">Loading services...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <section aria-labelledby="services-page-title">
        <h1 id="services-page-title" className="text-center mb-lg">
          Government Services
        </h1>
        
        <p className="text-center mb-xl" style={{ color: 'var(--color-text-secondary)', maxWidth: '600px', margin: '0 auto var(--spacing-xl)' }}>
          Select a service to view requirements and book an appointment.
          All services are available at Huduma Centers across Kenya.
        </p>

        <div className="services-grid" role="list">
          {services.map((service) => (
            <ServiceCard
              key={service.service_type}
              service={service}
              onSelect={handleServiceSelect}
            />
          ))}
        </div>
      </section>

      {/* Service Details Modal */}
      {selectedService && (
        <div 
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="service-details-title"
          onClick={(e) => e.target === e.currentTarget && handleCloseDetails()}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--spacing-lg)',
            zIndex: 1000,
          }}
        >
          <div 
            className="card"
            style={{
              maxWidth: '600px',
              width: '100%',
              maxHeight: '90vh',
              overflow: 'auto',
            }}
          >
            <div className="card-header">
              <h2 id="service-details-title" style={{ margin: 0 }}>
                {selectedService.name || selectedService.service_name}
              </h2>
            </div>
            
            <div className="card-body">
              <p style={{ marginBottom: 'var(--spacing-lg)', color: 'var(--color-text-secondary)' }}>
                {selectedService.description}
              </p>
              
              <h3 style={{ marginBottom: 'var(--spacing-sm)' }}>Department</h3>
              <p style={{ marginBottom: 'var(--spacing-lg)' }}>
                {selectedService.department}
              </p>
              
              <h3 style={{ marginBottom: 'var(--spacing-sm)' }}>Required Documents</h3>
              <ul style={{ paddingLeft: 'var(--spacing-lg)', marginBottom: 'var(--spacing-lg)' }}>
                {selectedService.requirements?.map((req, index) => (
                  <li key={index} style={{ marginBottom: 'var(--spacing-xs)' }}>
                    {req}
                  </li>
                ))}
              </ul>
              
              <h3 style={{ marginBottom: 'var(--spacing-sm)' }}>Available Time Slots</h3>
              <ul style={{ paddingLeft: 'var(--spacing-lg)', marginBottom: 'var(--spacing-lg)' }}>
                {selectedService.time_slots?.map((slot, index) => (
                  <li key={index} style={{ marginBottom: 'var(--spacing-xs)' }}>
                    {slot}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="card-footer" style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
              <button
                className="btn btn-secondary"
                onClick={handleCloseDetails}
                style={{ flex: 1 }}
              >
                Close
              </button>
              <a
                href={`/booking/${selectedService.service_type}`}
                className="btn btn-primary"
                style={{ flex: 1, textDecoration: 'none', textAlign: 'center' }}
              >
                Book Appointment
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ServicesPage;

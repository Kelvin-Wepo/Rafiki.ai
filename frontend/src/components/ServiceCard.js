/**
 * Service Card Component
 * Accessible card for displaying government services
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAccessibility } from '../context/AccessibilityContext';

// Service icons
const serviceIcons = {
  passport: (
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M6 2c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2H6zm0 2h12v16H6V4zm6 3c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3zm-4 9h8v1c0 .55-.45 1-1 1H9c-.55 0-1-.45-1-1v-1z"/>
    </svg>
  ),
  national_id: (
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H4V6h16v12zM6 10h2v2H6v-2zm0 4h8v2H6v-2zm10-4h2v6h-2v-6zm-4 0h2v2h-2v-2z"/>
    </svg>
  ),
  driving_license: (
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/>
    </svg>
  ),
  good_conduct: (
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 6c1.4 0 2.8 1.1 2.8 2.5V11c.6 0 1.2.6 1.2 1.2v3.5c0 .7-.6 1.3-1.2 1.3H9.2c-.7 0-1.2-.6-1.2-1.2v-3.5c0-.7.6-1.3 1.2-1.3V9.5C9.2 8.1 10.6 7 12 7zm0 1.2c-.8 0-1.5.5-1.5 1.3V11h3V9.5c0-.8-.7-1.3-1.5-1.3z"/>
    </svg>
  ),
};

function ServiceCard({ service, onSelect }) {
  const navigate = useNavigate();
  const { announce, speak, settings } = useAccessibility();

  const handleClick = () => {
    announce(`Selected ${service.name}`);
    if (settings.voiceEnabled) {
      speak(`You selected ${service.name}. ${service.description}`);
    }
    
    if (onSelect) {
      onSelect(service);
    } else {
      navigate(`/booking/${service.type || service.service_type}`);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  const serviceType = service.type || service.service_type;
  const Icon = serviceIcons[serviceType];

  return (
    <article
      className="service-card"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`${service.name}. ${service.description}. Press Enter to select.`}
    >
      <div className="service-card-icon" aria-hidden="true">
        {Icon || (
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-7-2h2v-4h4v-2h-4V7h-2v4H8v2h4v4z"/>
          </svg>
        )}
      </div>
      
      <h3 className="service-card-title">{service.name}</h3>
      
      <p className="service-card-description">{service.description}</p>
      
      <div 
        className="service-card-department"
        style={{ 
          marginTop: 'auto', 
          paddingTop: 'var(--spacing-md)',
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-muted)'
        }}
      >
        {service.department}
      </div>
    </article>
  );
}

export default ServiceCard;

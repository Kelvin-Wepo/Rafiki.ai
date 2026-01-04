/**
 * Time Slot Picker Component
 * Accessible time slot selection for appointments
 */

import React from 'react';
import { useAccessibility } from '../context/AccessibilityContext';

const timeSlots = [
  {
    id: 'morning',
    label: 'Morning',
    time: '8:00 AM - 12:00 PM',
    value: '08:00-12:00',
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.79 1.42-1.41zM4 10.5H1v2h3v-2zm9-9.95h-2V3.5h2V.55zm7.45 3.91l-1.41-1.41-1.79 1.79 1.41 1.41 1.79-1.79zm-3.21 13.7l1.79 1.8 1.41-1.41-1.8-1.79-1.4 1.4zM20 10.5v2h3v-2h-3zm-8-5c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm-1 16.95h2V19.5h-2v2.95zm-7.45-3.91l1.41 1.41 1.79-1.8-1.41-1.41-1.79 1.8z"/>
      </svg>
    ),
  },
  {
    id: 'afternoon',
    label: 'Afternoon',
    time: '2:00 PM - 5:00 PM',
    value: '14:00-17:00',
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58c-.39-.39-1.03-.39-1.41 0-.39.39-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37c-.39-.39-1.03-.39-1.41 0-.39.39-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0 .39-.39.39-1.03 0-1.41l-1.06-1.06zm1.06-10.96c.39-.39.39-1.03 0-1.41-.39-.39-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36c.39-.39.39-1.03 0-1.41-.39-.39-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06z"/>
      </svg>
    ),
  },
];

function TimeSlotPicker({ selectedSlot, onSelect, disabled = false }) {
  const { announce, speak, settings } = useAccessibility();

  const handleSelect = (slot) => {
    if (disabled) return;
    
    onSelect(slot.value);
    announce(`Selected ${slot.label} time slot: ${slot.time}`);
    
    if (settings.voiceEnabled) {
      speak(`You selected the ${slot.label} slot from ${slot.time}`);
    }
  };

  const handleKeyDown = (e, slot) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleSelect(slot);
    }
  };

  return (
    <div 
      className="time-slots"
      role="radiogroup"
      aria-label="Select appointment time"
    >
      {timeSlots.map((slot) => (
        <div
          key={slot.id}
          className={`time-slot ${selectedSlot === slot.value ? 'selected' : ''}`}
          onClick={() => handleSelect(slot)}
          onKeyDown={(e) => handleKeyDown(e, slot)}
          role="radio"
          aria-checked={selectedSlot === slot.value}
          tabIndex={disabled ? -1 : 0}
          aria-disabled={disabled}
          aria-label={`${slot.label}: ${slot.time}${selectedSlot === slot.value ? ' (selected)' : ''}`}
        >
          <div className="time-slot-icon" aria-hidden="true">
            {slot.icon}
          </div>
          <span className="time-slot-label">{slot.label}</span>
          <span className="time-slot-time">{slot.time}</span>
        </div>
      ))}
    </div>
  );
}

export default TimeSlotPicker;

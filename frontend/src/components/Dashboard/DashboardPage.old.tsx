/**
 * Dashboard Page Component
 * Main dashboard container that shows sidenav and content sections.
 * 
 * Responsive Layout:
 * - Desktop (≥1024px): Fixed sidebar + main content
 * - Tablet (≥768px <1024px): Collapsible sidebar
 * - Mobile (<768px): Off-canvas drawer with top navbar
 */

import React, { useState, useCallback, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Sidenav, ConversationHistory, TranscriptDownload } from '.';
import type { NavSection } from '.';
import type { Conversation } from '../../services/authService';
import { createConversation } from '../../services/authService';
import './Dashboard.css';

interface DashboardProps {
  children?: React.ReactNode;
}

export function Dashboard({ children }: DashboardProps) {
  const { user } = useAuth();
  const [activeSection, setActiveSection] = useState<NavSection>('new');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [isCreatingConversation, setIsCreatingConversation] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  // Return focus to menu button when drawer closes
  const handleMobileClose = useCallback(() => {
    setIsMobileMenuOpen(false);
    setTimeout(() => menuButtonRef.current?.focus(), 100);
  }, []);

  /**
   * Create a new conversation.
   */
  const handleNewConversation = useCallback(async () => {
    setIsCreatingConversation(true);
    try {
      const newConversation = await createConversation();
      setSelectedConversation(newConversation);
      setActiveSection('new');
    } catch (error) {
      console.error('Failed to create conversation:', error);
    } finally {
      setIsCreatingConversation(false);
    }
  }, []);

  /**
   * Select a conversation from history.
   */
  const handleSelectConversation = useCallback((conversation: Conversation) => {
    setSelectedConversation(conversation);
    setActiveSection('new');
  }, []);

  /**
   * Render section content based on active section.
   */
  const renderContent = () => {
    switch (activeSection) {
      case 'new':
        return (
          <div className="new-conversation-section">
            <div className="section-header">
              <div>
                <h2 className="section-title">
                  {selectedConversation ? 'Continue Conversation' : 'New Conversation'}
                </h2>
                <p className="section-subtitle">
                  {selectedConversation 
                    ? `Conversation: ${selectedConversation.title}`
                    : 'Ask Rafiki about government services'}
                </p>
              </div>
              <button 
                className="btn btn-primary"
                onClick={handleNewConversation}
                disabled={isCreatingConversation}
              >
                {isCreatingConversation ? (
                  <>
                    <span className="spinner" />
                    Creating...
                  </>
                ) : (
                  <>
                    <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 20, height: 20 }}>
                      <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
                    </svg>
                    New Chat
                  </>
                )}
              </button>
            </div>
            
            {/* Main content - children or placeholder */}
            {children || (
              <div className="conversation-placeholder">
                <div className="placeholder-content">
                  <div className="placeholder-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
                    </svg>
                  </div>
                  <h3>Welcome, {user?.phone_masked || 'User'}!</h3>
                  <p>
                    I'm Rafiki, your secure government services assistant.
                    How can I help you today?
                  </p>
                  <div className="quick-actions">
                    <button className="quick-action-btn">
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                      </svg>
                      Document Services
                    </button>
                    <button className="quick-action-btn">
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M21 18v1c0 1.1-.9 2-2 2H5c-1.11 0-2-.9-2-2V5c0-1.1.89-2 2-2h14c1.1 0 2 .9 2 2v1h-9c-1.11 0-2 .9-2 2v8c0 1.1.89 2 2 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
                      </svg>
                      Tax Services (KRA)
                    </button>
                    <button className="quick-action-btn">
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/>
                      </svg>
                      General Inquiry
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case 'history':
        return (
          <ConversationHistory
            onSelectConversation={handleSelectConversation}
            selectedId={selectedConversation?.id}
            onNewConversation={handleNewConversation}
          />
        );

      case 'transcripts':
        return (
          <TranscriptDownload preSelectedConversation={selectedConversation} />
        );

      case 'profile':
        return (
          <div className="profile-section">
            <div className="section-header">
              <h2 className="section-title">Your Profile</h2>
              <p className="section-subtitle">Manage your account settings</p>
            </div>

            <div className="profile-card">
              <div className="profile-avatar">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
              </div>
              <div className="profile-info">
                <h3>{user?.phone_masked || 'User'}</h3>
                <span className="profile-status">
                  <span className="status-dot" />
                  Active
                </span>
              </div>
            </div>

            <div className="profile-details">
              <div className="detail-row">
                <span className="detail-label">User ID</span>
                <span className="detail-value">{user?.user_id || '-'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Account Status</span>
                <span className="detail-value status-badge">{user?.status || 'active'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Member Since</span>
                <span className="detail-value">
                  {user?.created_at
                    ? new Date(user.created_at).toLocaleDateString('en-KE', {
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric',
                      })
                    : '-'}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Last Login</span>
                <span className="detail-value">
                  {user?.last_login
                    ? new Date(user.last_login).toLocaleString('en-KE')
                    : 'First session'}
                </span>
              </div>
            </div>

            <div className="security-info">
              <h4>
                <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 20, height: 20 }}>
                  <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
                </svg>
                Security
              </h4>
              <p>Your session is protected with government-grade encryption.</p>
              <ul>
                <li>Phone-based authentication (OTP)</li>
                <li>AES-256 data encryption</li>
                <li>Automatic session timeout</li>
                <li>Audit logging enabled</li>
              </ul>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidenav
        activeSection={activeSection}
        onSectionChange={setActiveSection}
        isMobileOpen={isMobileMenuOpen}
        onMobileClose={handleMobileClose}
      />

      <main className="dashboard-main">
        {/* Mobile/Tablet Header */}
        <header className="mobile-header">
          <button
            ref={menuButtonRef}
            className="mobile-menu-btn"
            onClick={() => setIsMobileMenuOpen(true)}
            aria-label="Open menu"
            aria-expanded={isMobileMenuOpen}
            aria-controls="sidenav"
          >
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
            </svg>
          </button>
          
          <div className="mobile-brand">
            <svg viewBox="0 0 24 24" fill="currentColor" className="mobile-logo">
              <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z" />
            </svg>
            <div className="mobile-brand-text">
              <h1 className="mobile-title">Rafiki</h1>
              <span className="mobile-subtitle">Government Services</span>
            </div>
          </div>
          
          <button 
            className="mobile-new-chat-btn"
            onClick={handleNewConversation}
            disabled={isCreatingConversation}
            aria-label="New conversation"
          >
            {isCreatingConversation ? (
              <span className="spinner-small" />
            ) : (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
              </svg>
            )}
            <span className="mobile-btn-text">New Chat</span>
          </button>
        </header>

        <div className="dashboard-content">
          <div className="content-container">
            {renderContent()}
          </div>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;

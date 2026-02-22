/**
 * AppShell Component - Kenya National Design System
 * Main layout wrapper with header, sidebar, content, and footer
 */

import { useState, type ReactNode } from 'react';
import { GovHeader } from './GovHeader';
import { GovSidebar, type NavSection } from './GovSidebar';
import { GovFooter } from './GovFooter';
import type { Language } from '../ui/LanguageToggle';
import type { User } from '../../services/authService';

interface AppShellProps {
  children: ReactNode;
  user: User | null;
  onLogout: () => void;
  activeSection?: NavSection;
  onSectionChange?: (section: NavSection) => void;
  onNewChat?: () => void;
  showSidebar?: boolean;
  showFooter?: boolean;
}

export function AppShell({
  children,
  user,
  onLogout,
  activeSection = 'chat',
  onSectionChange,
  onNewChat,
  showSidebar = true,
  showFooter = false,
}: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [language, setLanguage] = useState<Language>('en');

  const handleSectionChange = (section: NavSection) => {
    onSectionChange?.(section);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--ke-gray-50)]">
      {/* Skip to main content link for accessibility */}
      <a href="#main-content" className="skip-link">
        {language === 'sw' ? 'Ruka hadi maudhui kuu' : 'Skip to main content'}
      </a>

      {/* Government Header */}
      <GovHeader
        user={user}
        onLogout={onLogout}
        onMenuClick={() => setSidebarOpen(true)}
        language={language}
        onLanguageChange={setLanguage}
        showMobileMenu={showSidebar}
      />

      {/* Main layout */}
      <div className="flex flex-1">
        {/* Sidebar */}
        {showSidebar && (
          <GovSidebar
            isOpen={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
            activeSection={activeSection}
            onSectionChange={handleSectionChange}
            isCollapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
            language={language}
            onNewChat={onNewChat}
          />
        )}

        {/* Main content */}
        <main
          id="main-content"
          tabIndex={-1}
          className={`
            flex-1 min-w-0
            transition-all duration-300
            ${showSidebar && !sidebarCollapsed ? 'lg:ml-0' : ''}
          `}
        >
          <div className="h-full">
            {children}
          </div>
        </main>
      </div>

      {/* Footer */}
      {showFooter && <GovFooter language={language} />}
    </div>
  );
}

export default AppShell;

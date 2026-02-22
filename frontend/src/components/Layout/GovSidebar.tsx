/**
 * Government Navigation Sidebar - Kenya National Design System
 * Accessible navigation for desktop and mobile
 */

import { useState, useEffect, useRef, type ReactNode } from 'react';
import {
  MessageSquarePlus,
  History,
  FileText,
  HelpCircle,
  Settings,
  MessageSquareWarning,
  ChevronLeft,
  ChevronRight,
  X,
  Shield,
} from 'lucide-react';
import type { Language } from '../ui/LanguageToggle';

export type NavSection = 'chat' | 'history' | 'transcripts' | 'help' | 'settings' | 'feedback';

interface NavItem {
  id: NavSection;
  labelEn: string;
  labelSw: string;
  icon: ReactNode;
  badge?: number;
}

const navItems: NavItem[] = [
  { id: 'chat', labelEn: 'New Chat', labelSw: 'Gumzo Mpya', icon: <MessageSquarePlus className="w-5 h-5" /> },
  { id: 'history', labelEn: 'History', labelSw: 'Historia', icon: <History className="w-5 h-5" /> },
  { id: 'transcripts', labelEn: 'Transcripts', labelSw: 'Nakala', icon: <FileText className="w-5 h-5" /> },
];

const bottomNavItems: NavItem[] = [
  { id: 'help', labelEn: 'Help', labelSw: 'Msaada', icon: <HelpCircle className="w-5 h-5" /> },
  { id: 'feedback', labelEn: 'Feedback', labelSw: 'Maoni', icon: <MessageSquareWarning className="w-5 h-5" /> },
  { id: 'settings', labelEn: 'Settings', labelSw: 'Mipangilio', icon: <Settings className="w-5 h-5" /> },
];

interface GovSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeSection: NavSection;
  onSectionChange: (section: NavSection) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  language: Language;
  onNewChat?: () => void;
}

export function GovSidebar({
  isOpen,
  onClose,
  activeSection,
  onSectionChange,
  isCollapsed,
  onToggleCollapse,
  language,
  onNewChat,
}: GovSidebarProps) {
  const sidebarRef = useRef<HTMLElement>(null);
  const [focusedIndex, setFocusedIndex] = useState(-1);

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Focus trap for mobile overlay
  useEffect(() => {
    if (isOpen && window.innerWidth < 1024) {
      sidebarRef.current?.focus();
    }
  }, [isOpen]);

  const handleNavClick = (item: NavItem) => {
    if (item.id === 'chat' && onNewChat) {
      onNewChat();
    }
    onSectionChange(item.id);
    if (window.innerWidth < 1024) {
      onClose();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, index: number, items: NavItem[]) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setFocusedIndex((index + 1) % items.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setFocusedIndex((index - 1 + items.length) % items.length);
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleNavClick(items[index]);
    }
  };

  const getLabel = (item: NavItem) => (language === 'sw' ? item.labelSw : item.labelEn);

  const renderNavItem = (item: NavItem, index: number, items: NavItem[], section: 'main' | 'bottom') => {
    const isActive = activeSection === item.id;
    const actualIndex = section === 'bottom' ? index + navItems.length : index;

    return (
      <li key={item.id}>
        <button
          type="button"
          onClick={() => handleNavClick(item)}
          onKeyDown={(e) => handleKeyDown(e, index, items)}
          tabIndex={focusedIndex === actualIndex ? 0 : -1}
          aria-current={isActive ? 'page' : undefined}
          className={`
            w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
            text-sm font-medium transition-all duration-200
            min-h-[44px]
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ke-green)] focus-visible:ring-inset
            ${isActive
              ? 'bg-[var(--ke-green)] text-white'
              : 'text-[var(--ke-gray-700)] hover:bg-[var(--ke-gray-100)] hover:text-[var(--ke-gray-900)]'
            }
            ${isCollapsed ? 'justify-center' : ''}
          `}
          title={isCollapsed ? getLabel(item) : undefined}
        >
          <span className={`flex-shrink-0 ${isActive ? 'text-white' : 'text-[var(--ke-gray-500)]'}`}>
            {item.icon}
          </span>
          {!isCollapsed && (
            <>
              <span className="flex-1 text-left">{getLabel(item)}</span>
              {item.badge && (
                <span className="px-2 py-0.5 text-xs font-semibold bg-[var(--ke-red)] text-white rounded-full">
                  {item.badge}
                </span>
              )}
            </>
          )}
        </button>
      </li>
    );
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[var(--z-modal-backdrop)] lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        ref={sidebarRef}
        id="sidebar"
        tabIndex={-1}
        role="navigation"
        aria-label={language === 'sw' ? 'Urambazaji kuu' : 'Main navigation'}
        className={`
          fixed lg:sticky top-0 left-0 z-[var(--z-modal)] lg:z-auto
          h-screen lg:h-[calc(100vh-var(--header-height))]
          bg-white border-r border-[var(--ke-gray-200)]
          transform transition-all duration-300 ease-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          ${isCollapsed ? 'w-[72px]' : 'w-64'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Mobile header */}
          <div className="flex items-center justify-between p-4 border-b border-[var(--ke-gray-200)] lg:hidden">
            <div className="flex items-center gap-2">
              <Shield className="w-6 h-6 text-[var(--ke-green)]" />
              <span className="font-bold text-[var(--ke-gray-900)]">Rafiki</span>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 text-[var(--ke-gray-500)] hover:text-[var(--ke-gray-900)] hover:bg-[var(--ke-gray-100)] rounded-lg min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label={language === 'sw' ? 'Funga menyu' : 'Close menu'}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Collapse toggle (desktop) */}
          <div className="hidden lg:flex items-center justify-end p-2 border-b border-[var(--ke-gray-200)]">
            <button
              type="button"
              onClick={onToggleCollapse}
              className="p-2 text-[var(--ke-gray-500)] hover:text-[var(--ke-gray-900)] hover:bg-[var(--ke-gray-100)] rounded-lg"
              aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>

          {/* Main navigation */}
          <nav className="flex-1 overflow-y-auto p-3">
            <ul className="space-y-1" role="menubar">
              {navItems.map((item, index) => renderNavItem(item, index, navItems, 'main'))}
            </ul>
          </nav>

          {/* Bottom navigation */}
          <div className="border-t border-[var(--ke-gray-200)] p-3">
            <ul className="space-y-1" role="menubar">
              {bottomNavItems.map((item, index) => renderNavItem(item, index, bottomNavItems, 'bottom'))}
            </ul>
          </div>
        </div>
      </aside>
    </>
  );
}

export default GovSidebar;

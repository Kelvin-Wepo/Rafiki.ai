/**
 * Sidebar Component - Revamped with Collapsible Design
 * 
 * Features:
 * - Collapsible on all screen sizes (icon-only mode)
 * - Smooth animations and hover expansions
 * - Modern glass morphism design
 * - Tooltips when collapsed
 * - Logout confirmation dialog
 */

import { useState } from 'react';
import {
  MessageSquarePlus,
  History,
  FileText,
  LogOut,
  X,
  Shield,
  ChevronLeft,
  ChevronRight,
  Settings,
  HelpCircle,
  AlertTriangle,
} from 'lucide-react';
import type { User } from '../../services/authService';
import '../Auth/Auth.css';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
  onNewChat: () => void;
  onLogout: () => void;
  currentView: 'chat' | 'history' | 'transcripts';
  onViewChange: (view: 'chat' | 'history' | 'transcripts') => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export default function Sidebar({
  isOpen,
  onClose,
  user,
  onNewChat,
  onLogout,
  currentView,
  onViewChange,
  isCollapsed,
  onToggleCollapse,
}: SidebarProps) {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const navItems = [
    { id: 'chat' as const, label: 'New Chat', icon: MessageSquarePlus, action: onNewChat },
    { id: 'history' as const, label: 'History', icon: History, action: undefined },
    { id: 'transcripts' as const, label: 'Transcripts', icon: FileText, action: undefined },
  ];

  const bottomNavItems = [
    { id: 'help', label: 'Help', icon: HelpCircle },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const handleLogoutClick = () => {
    setShowLogoutConfirm(true);
  };

  const handleLogoutConfirm = () => {
    setShowLogoutConfirm(false);
    onLogout();
  };

  const handleLogoutCancel = () => {
    setShowLogoutConfirm(false);
  };

  return (
    <>
      {/* Logout Confirmation Dialog */}
      {showLogoutConfirm && (
        <div className="confirm-overlay" onClick={handleLogoutCancel}>
          <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="confirm-icon">
              <AlertTriangle />
            </div>
            <h3 className="confirm-title">Sign Out?</h3>
            <p className="confirm-message">
              Are you sure you want to sign out? You'll need to verify your phone number again to access your account.
            </p>
            <div className="confirm-actions">
              <button className="confirm-cancel" onClick={handleLogoutCancel}>
                Cancel
              </button>
              <button className="confirm-confirm" onClick={handleLogoutConfirm}>
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Overlay */}
      <div
        className={`
          fixed inset-0 bg-black/70 backdrop-blur-md z-40
          transition-all duration-300 md:hidden
          ${isOpen ? 'opacity-100 visible' : 'opacity-0 invisible pointer-events-none'}
        `}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sidebar */}
      <aside
        id="sidebar"
        role="navigation"
        aria-label="Main navigation"
        className={`
          fixed md:relative top-0 left-0 z-50 h-full
          bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950
          border-r border-slate-700/50
          flex flex-col
          transition-all duration-300 ease-in-out
          shadow-2xl shadow-black/50
          ${isCollapsed ? 'w-[72px]' : 'w-[260px]'}
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        {/* Header */}
        <div className={`
          flex items-center h-16 px-4 border-b border-slate-700/50
          ${isCollapsed ? 'justify-center' : 'justify-between'}
        `}>
          {/* Logo */}
          <div className={`flex items-center gap-3 ${isCollapsed ? 'justify-center' : ''}`}>
            <div className="relative group">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-400 to-cyan-500 rounded-xl blur-md opacity-50 group-hover:opacity-75 transition-opacity" />
              <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center shadow-lg">
                <span className="text-white font-black text-xl">R</span>
              </div>
            </div>
            {!isCollapsed && (
              <div className="overflow-hidden">
                <h1 className="text-white font-bold text-lg tracking-tight">Rafiki</h1>
                <p className="text-slate-400 text-[10px] font-medium uppercase tracking-wider">AI Assistant</p>
              </div>
            )}
          </div>
          
          {/* Close button - mobile only */}
          <button
            onClick={onClose}
            className="md:hidden p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Collapse toggle - desktop only */}
          {!isCollapsed && (
            <button
              onClick={onToggleCollapse}
              className="hidden md:flex p-2 text-slate-400 hover:text-white hover:bg-slate-800/50 rounded-lg transition-all"
              aria-label="Collapse sidebar"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Expand button when collapsed */}
        {isCollapsed && (
          <button
            onClick={onToggleCollapse}
            className="hidden md:flex mx-auto mt-4 p-2 text-slate-400 hover:text-white hover:bg-slate-800/50 rounded-lg transition-all"
            aria-label="Expand sidebar"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        )}

        {/* New Chat Button */}
        <div className={`px-3 ${isCollapsed ? 'mt-4' : 'mt-6'}`}>
          <button
            onClick={() => {
              onNewChat();
              onClose();
            }}
            onMouseEnter={() => setHoveredItem('newchat')}
            onMouseLeave={() => setHoveredItem(null)}
            className={`
              relative w-full flex items-center gap-3 
              bg-gradient-to-r from-emerald-500 to-cyan-500
              hover:from-emerald-400 hover:to-cyan-400
              text-white font-semibold rounded-xl
              transition-all duration-200 shadow-lg shadow-emerald-500/20
              hover:shadow-emerald-500/40 hover:scale-[1.02]
              ${isCollapsed ? 'p-3 justify-center' : 'px-4 py-3'}
            `}
          >
            <MessageSquarePlus className="w-5 h-5 flex-shrink-0" />
            {!isCollapsed && <span>New Chat</span>}
            
            {/* Tooltip when collapsed */}
            {isCollapsed && hoveredItem === 'newchat' && (
              <div className="absolute left-full ml-3 px-3 py-2 bg-slate-800 text-white text-sm rounded-lg whitespace-nowrap z-50 shadow-xl">
                New Chat
                <div className="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 w-2 h-2 bg-slate-800 rotate-45" />
              </div>
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className={`flex-1 overflow-y-auto py-4 ${isCollapsed ? 'px-2' : 'px-3'}`}>
          <div className="space-y-1">
            {navItems.slice(1).map((item) => {
              const Icon = item.icon;
              const isActive = item.id === currentView;
              
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    if (item.action) {
                      item.action();
                    } else {
                      onViewChange(item.id);
                    }
                    onClose();
                  }}
                  onMouseEnter={() => setHoveredItem(item.id)}
                  onMouseLeave={() => setHoveredItem(null)}
                  className={`
                    relative w-full flex items-center gap-3 rounded-xl
                    transition-all duration-200
                    ${isCollapsed ? 'p-3 justify-center' : 'px-4 py-3'}
                    ${isActive
                      ? 'bg-slate-800/80 text-emerald-400 shadow-inner'
                      : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
                    }
                  `}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-emerald-400' : ''}`} />
                  {!isCollapsed && <span className="font-medium">{item.label}</span>}
                  
                  {/* Active indicator */}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-r-full" />
                  )}
                  
                  {/* Tooltip when collapsed */}
                  {isCollapsed && hoveredItem === item.id && (
                    <div className="absolute left-full ml-3 px-3 py-2 bg-slate-800 text-white text-sm rounded-lg whitespace-nowrap z-50 shadow-xl">
                      {item.label}
                      <div className="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 w-2 h-2 bg-slate-800 rotate-45" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Divider */}
          <div className={`my-6 border-t border-slate-700/50 ${isCollapsed ? 'mx-2' : 'mx-2'}`} />

          {/* Bottom nav items */}
          <div className="space-y-1">
            {bottomNavItems.map((item) => {
              const Icon = item.icon;
              
              return (
                <button
                  key={item.id}
                  onMouseEnter={() => setHoveredItem(item.id)}
                  onMouseLeave={() => setHoveredItem(null)}
                  className={`
                    relative w-full flex items-center gap-3 rounded-xl
                    text-slate-500 hover:bg-slate-800/50 hover:text-slate-300
                    transition-all duration-200
                    ${isCollapsed ? 'p-3 justify-center' : 'px-4 py-3'}
                  `}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  {!isCollapsed && <span className="font-medium text-sm">{item.label}</span>}
                  
                  {/* Tooltip when collapsed */}
                  {isCollapsed && hoveredItem === item.id && (
                    <div className="absolute left-full ml-3 px-3 py-2 bg-slate-800 text-white text-sm rounded-lg whitespace-nowrap z-50 shadow-xl">
                      {item.label}
                      <div className="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 w-2 h-2 bg-slate-800 rotate-45" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </nav>

        {/* User Info Section */}
        <div className={`border-t border-slate-700/50 ${isCollapsed ? 'p-2' : 'p-4'}`}>
          {/* User Profile */}
          <div 
            className={`
              relative flex items-center gap-3 p-3 rounded-xl
              bg-slate-800/30 hover:bg-slate-800/50 transition-all cursor-pointer
              ${isCollapsed ? 'justify-center' : ''}
            `}
            onMouseEnter={() => setHoveredItem('user')}
            onMouseLeave={() => setHoveredItem(null)}
          >
            <div className="relative">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center ring-2 ring-slate-700">
                <span className="text-white font-bold text-sm">
                  {user?.phone_masked?.slice(-2) || 'U'}
                </span>
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 border-2 border-slate-900" />
            </div>
            {!isCollapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-medium truncate">
                  {user?.phone_masked || 'Guest'}
                </p>
                <p className="text-emerald-400 text-xs font-medium">Online</p>
              </div>
            )}
            
            {/* Tooltip when collapsed */}
            {isCollapsed && hoveredItem === 'user' && (
              <div className="absolute left-full ml-3 px-3 py-2 bg-slate-800 text-white text-sm rounded-lg whitespace-nowrap z-50 shadow-xl">
                {user?.phone_masked || 'Guest'} • Online
                <div className="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 w-2 h-2 bg-slate-800 rotate-45" />
              </div>
            )}
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogoutClick}
            onMouseEnter={() => setHoveredItem('logout')}
            onMouseLeave={() => setHoveredItem(null)}
            className={`
              relative w-full flex items-center gap-3 mt-2 rounded-xl
              text-slate-500 hover:text-red-400 hover:bg-red-500/10
              transition-all duration-200
              ${isCollapsed ? 'p-3 justify-center' : 'px-4 py-2.5'}
            `}
            aria-label="Logout"
          >
            <LogOut className="w-5 h-5" />
            {!isCollapsed && <span className="font-medium text-sm">Logout</span>}
            
            {/* Tooltip when collapsed */}
            {isCollapsed && hoveredItem === 'logout' && (
              <div className="absolute left-full ml-3 px-3 py-2 bg-slate-800 text-white text-sm rounded-lg whitespace-nowrap z-50 shadow-xl">
                Logout
                <div className="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 w-2 h-2 bg-slate-800 rotate-45" />
              </div>
            )}
          </button>

          {/* Security Badge */}
          {!isCollapsed && (
            <div className="flex items-center justify-center gap-2 mt-4 py-2 text-slate-600 text-xs">
              <Shield className="w-3.5 h-3.5" />
              <span>End-to-end encrypted</span>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

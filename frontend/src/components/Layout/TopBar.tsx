/**
 * TopBar Component - Revamped
 * Mobile header with hamburger menu and actions
 */

import { Menu, Plus } from 'lucide-react';

interface TopBarProps {
  onMenuClick: () => void;
  onNewChat: () => void;
  title?: string;
}

export default function TopBar({ onMenuClick, onNewChat, title = 'Rafiki' }: TopBarProps) {
  return (
    <header className="md:hidden sticky top-0 z-30 bg-slate-900/80 backdrop-blur-xl border-b border-slate-700/50">
      <div className="flex items-center justify-between px-4 h-16">
        {/* Menu Button */}
        <button
          onClick={onMenuClick}
          className="p-2.5 -ml-1 text-slate-300 hover:text-white hover:bg-slate-800/50 rounded-xl transition-all min-w-[44px] min-h-[44px] flex items-center justify-center"
          aria-label="Open menu"
          aria-expanded="false"
          aria-controls="sidebar"
        >
          <Menu className="w-6 h-6" />
        </button>

        {/* Logo & Title */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center">
            <span className="text-white font-bold text-sm">R</span>
          </div>
          <h1 className="text-white font-bold text-lg">{title}</h1>
        </div>

        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          className="flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white text-sm font-semibold rounded-xl hover:from-emerald-400 hover:to-cyan-400 transition-all min-h-[44px] shadow-lg shadow-emerald-500/20"
          aria-label="Start new chat"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">New</span>
        </button>
      </div>
    </header>
  );
}

/**
 * Tabs Component - Kenya National Design System
 * Accessible tabbed interface
 */

import { useState, useRef, type ReactNode, type KeyboardEvent } from 'react';

export interface Tab {
  id: string;
  label: string;
  icon?: ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: Tab[];
  defaultTab?: string;
  activeTab?: string;
  onChange?: (tabId: string) => void;
  children: (activeTabId: string) => ReactNode;
  variant?: 'underline' | 'pills' | 'enclosed';
  fullWidth?: boolean;
}

export function Tabs({
  tabs,
  defaultTab,
  activeTab: controlledActiveTab,
  onChange,
  children,
  variant = 'underline',
  fullWidth = false,
}: TabsProps) {
  const [internalActiveTab, setInternalActiveTab] = useState(defaultTab || tabs[0]?.id);
  const tabRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  const activeTab = controlledActiveTab ?? internalActiveTab;

  const handleTabClick = (tabId: string) => {
    if (onChange) {
      onChange(tabId);
    } else {
      setInternalActiveTab(tabId);
    }
  };

  const handleKeyDown = (e: KeyboardEvent, currentIndex: number) => {
    const enabledTabs = tabs.filter(t => !t.disabled);
    const currentEnabledIndex = enabledTabs.findIndex(t => t.id === tabs[currentIndex].id);

    let newIndex: number | null = null;

    if (e.key === 'ArrowRight') {
      newIndex = (currentEnabledIndex + 1) % enabledTabs.length;
    } else if (e.key === 'ArrowLeft') {
      newIndex = (currentEnabledIndex - 1 + enabledTabs.length) % enabledTabs.length;
    } else if (e.key === 'Home') {
      newIndex = 0;
    } else if (e.key === 'End') {
      newIndex = enabledTabs.length - 1;
    }

    if (newIndex !== null) {
      e.preventDefault();
      const newTab = enabledTabs[newIndex];
      handleTabClick(newTab.id);
      tabRefs.current.get(newTab.id)?.focus();
    }
  };

  const variants = {
    underline: {
      list: 'border-b border-[var(--ke-gray-200)]',
      tab: (isActive: boolean) => `
        relative px-4 py-3 font-medium transition-colors
        ${isActive
          ? 'text-[var(--ke-green)]'
          : 'text-[var(--ke-gray-600)] hover:text-[var(--ke-gray-900)]'
        }
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ke-green)] focus-visible:ring-inset
        disabled:opacity-50 disabled:cursor-not-allowed
      `,
      indicator: 'absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--ke-green)]',
    },
    pills: {
      list: 'bg-[var(--ke-gray-100)] p-1 rounded-lg',
      tab: (isActive: boolean) => `
        px-4 py-2 rounded-md font-medium transition-all
        ${isActive
          ? 'bg-white text-[var(--ke-gray-900)] shadow-sm'
          : 'text-[var(--ke-gray-600)] hover:text-[var(--ke-gray-900)]'
        }
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ke-green)]
        disabled:opacity-50 disabled:cursor-not-allowed
      `,
      indicator: '',
    },
    enclosed: {
      list: 'border-b border-[var(--ke-gray-200)]',
      tab: (isActive: boolean) => `
        px-4 py-3 font-medium transition-all border-b-2 -mb-px
        ${isActive
          ? 'bg-white border-[var(--ke-green)] text-[var(--ke-green)] rounded-t-lg border-x border-t border-[var(--ke-gray-200)]'
          : 'border-transparent text-[var(--ke-gray-600)] hover:text-[var(--ke-gray-900)] hover:border-[var(--ke-gray-300)]'
        }
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ke-green)]
        disabled:opacity-50 disabled:cursor-not-allowed
      `,
      indicator: '',
    },
  };

  const style = variants[variant];

  return (
    <div>
      <div
        role="tablist"
        aria-label="Tabs"
        className={`flex ${fullWidth ? '' : 'inline-flex'} ${style.list}`}
      >
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            ref={(el) => {
              if (el) tabRefs.current.set(tab.id, el);
            }}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`tabpanel-${tab.id}`}
            id={`tab-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            disabled={tab.disabled}
            onClick={() => handleTabClick(tab.id)}
            onKeyDown={(e) => handleKeyDown(e, index)}
            className={`
              ${fullWidth ? 'flex-1' : ''}
              ${style.tab(activeTab === tab.id)}
              flex items-center justify-center gap-2
            `.replace(/\s+/g, ' ').trim()}
          >
            {tab.icon}
            {tab.label}
            {variant === 'underline' && activeTab === tab.id && (
              <span className={style.indicator} />
            )}
          </button>
        ))}
      </div>

      <div
        role="tabpanel"
        id={`tabpanel-${activeTab}`}
        aria-labelledby={`tab-${activeTab}`}
        tabIndex={0}
        className="mt-4 focus-visible:outline-none"
      >
        {children(activeTab)}
      </div>
    </div>
  );
}

export default Tabs;

/**
 * Empty State Component - Kenya National Design System
 * Friendly empty states with call-to-action
 */

import { type ReactNode } from 'react';
import { FileQuestion, Search, Inbox, MessageSquare } from 'lucide-react';
import Button from './Button';

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  variant?: 'default' | 'search' | 'inbox' | 'conversation';
}

const defaultIcons = {
  default: FileQuestion,
  search: Search,
  inbox: Inbox,
  conversation: MessageSquare,
};

export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  variant = 'default',
}: EmptyStateProps) {
  const IconComponent = defaultIcons[variant];

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="w-16 h-16 rounded-full bg-[var(--ke-gray-100)] flex items-center justify-center mb-4">
        {icon || <IconComponent className="w-8 h-8 text-[var(--ke-gray-400)]" aria-hidden="true" />}
      </div>

      <h3 className="text-lg font-semibold text-[var(--ke-gray-900)] mb-2">
        {title}
      </h3>

      <p className="text-[var(--ke-gray-600)] max-w-sm mb-6">
        {description}
      </p>

      {(action || secondaryAction) && (
        <div className="flex flex-col sm:flex-row gap-3">
          {action && (
            <Button onClick={action.onClick}>
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button variant="ghost" onClick={secondaryAction.onClick}>
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// Pre-configured empty states
export function NoResultsFound({ onClear }: { onClear?: () => void }) {
  return (
    <EmptyState
      variant="search"
      title="No results found"
      description="We could not find what you are looking for. Try adjusting your search."
      action={onClear ? { label: 'Clear search', onClick: onClear } : undefined}
    />
  );
}

export function NoConversations({ onStart }: { onStart: () => void }) {
  return (
    <EmptyState
      variant="conversation"
      title="No conversations yet"
      description="Start a new conversation with Rafiki to get help with government services."
      action={{ label: 'Start conversation', onClick: onStart }}
    />
  );
}

export function InboxEmpty() {
  return (
    <EmptyState
      variant="inbox"
      title="Your inbox is empty"
      description="Messages and notifications will appear here."
    />
  );
}

export default EmptyState;

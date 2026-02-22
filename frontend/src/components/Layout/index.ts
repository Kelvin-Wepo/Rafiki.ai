/**
 * Layout Components Export
 * Kenya National Design System
 */

// New Government-grade components
export { AppShell } from './AppShell';
export { GovHeader } from './GovHeader';
export { GovFooter } from './GovFooter';
export { GovSidebar } from './GovSidebar';
export type { NavSection } from './GovSidebar';

// Existing components (for backward compatibility)
export { default as MainLayout } from './MainLayout';
export { default as Sidebar } from './Sidebar';
export { default as TopBar } from './TopBar';
export { default as AssistantPanel } from './AssistantPanel';
export { default as InteractionArea } from './InteractionArea';
export { default as ChatInput } from './ChatInput';
export { default as SystemMessage, SystemMessageInline } from './SystemMessage';
export type { MessageType } from './SystemMessage';

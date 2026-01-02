import { useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for keyboard navigation with accessibility support
 * Provides focus management and keyboard shortcuts
 */
const useKeyboardNavigation = (options = {}) => {
  const {
    containerRef = null,
    onEscape = () => {},
    onEnter = () => {},
    shortcuts = {},
    trapFocus = false,
    autoFocus = false
  } = options;

  const focusableElementsRef = useRef([]);
  const currentFocusIndexRef = useRef(0);

  // Get all focusable elements within a container
  const getFocusableElements = useCallback((container) => {
    if (!container) return [];
    
    const focusableSelectors = [
      'button:not([disabled])',
      'a[href]',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ].join(', ');

    return Array.from(container.querySelectorAll(focusableSelectors))
      .filter(el => {
        // Filter out hidden elements
        const style = window.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden';
      });
  }, []);

  // Focus the first focusable element
  const focusFirst = useCallback(() => {
    const container = containerRef?.current || document;
    const elements = getFocusableElements(container);
    if (elements.length > 0) {
      elements[0].focus();
      currentFocusIndexRef.current = 0;
    }
  }, [containerRef, getFocusableElements]);

  // Focus the last focusable element
  const focusLast = useCallback(() => {
    const container = containerRef?.current || document;
    const elements = getFocusableElements(container);
    if (elements.length > 0) {
      elements[elements.length - 1].focus();
      currentFocusIndexRef.current = elements.length - 1;
    }
  }, [containerRef, getFocusableElements]);

  // Focus next element
  const focusNext = useCallback(() => {
    const container = containerRef?.current || document;
    const elements = getFocusableElements(container);
    
    if (elements.length === 0) return;
    
    currentFocusIndexRef.current = (currentFocusIndexRef.current + 1) % elements.length;
    elements[currentFocusIndexRef.current].focus();
  }, [containerRef, getFocusableElements]);

  // Focus previous element
  const focusPrevious = useCallback(() => {
    const container = containerRef?.current || document;
    const elements = getFocusableElements(container);
    
    if (elements.length === 0) return;
    
    currentFocusIndexRef.current = currentFocusIndexRef.current <= 0 
      ? elements.length - 1 
      : currentFocusIndexRef.current - 1;
    elements[currentFocusIndexRef.current].focus();
  }, [containerRef, getFocusableElements]);

  // Focus element by index
  const focusByIndex = useCallback((index) => {
    const container = containerRef?.current || document;
    const elements = getFocusableElements(container);
    
    if (index >= 0 && index < elements.length) {
      elements[index].focus();
      currentFocusIndexRef.current = index;
    }
  }, [containerRef, getFocusableElements]);

  // Check if keyboard shortcut matches
  const matchesShortcut = useCallback((event, shortcut) => {
    const keys = shortcut.toLowerCase().split('+');
    const modifiers = {
      ctrl: event.ctrlKey,
      alt: event.altKey,
      shift: event.shiftKey,
      meta: event.metaKey
    };

    const key = keys[keys.length - 1];
    const requiredModifiers = keys.slice(0, -1);

    // Check if all required modifiers are pressed
    const modifiersMatch = requiredModifiers.every(mod => modifiers[mod]);
    
    // Check if no extra modifiers are pressed
    const noExtraModifiers = Object.entries(modifiers)
      .filter(([mod]) => !requiredModifiers.includes(mod))
      .every(([, pressed]) => !pressed);

    // Check if the key matches
    const keyMatches = event.key.toLowerCase() === key || 
                       event.code.toLowerCase() === `key${key}` ||
                       event.code.toLowerCase() === key;

    return modifiersMatch && noExtraModifiers && keyMatches;
  }, []);

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Handle custom shortcuts
      for (const [shortcut, handler] of Object.entries(shortcuts)) {
        if (matchesShortcut(event, shortcut)) {
          event.preventDefault();
          handler(event);
          return;
        }
      }

      // Handle escape key
      if (event.key === 'Escape') {
        onEscape(event);
        return;
      }

      // Handle enter key
      if (event.key === 'Enter' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)) {
        onEnter(event);
        return;
      }

      // Handle focus trapping
      if (trapFocus && event.key === 'Tab') {
        const container = containerRef?.current;
        if (!container) return;

        const elements = getFocusableElements(container);
        if (elements.length === 0) return;

        const firstElement = elements[0];
        const lastElement = elements[elements.length - 1];

        if (event.shiftKey && document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        } else if (!event.shiftKey && document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts, onEscape, onEnter, trapFocus, containerRef, getFocusableElements, matchesShortcut]);

  // Auto focus first element on mount
  useEffect(() => {
    if (autoFocus) {
      // Small delay to ensure DOM is ready
      const timer = setTimeout(focusFirst, 100);
      return () => clearTimeout(timer);
    }
  }, [autoFocus, focusFirst]);

  // Update focusable elements list
  useEffect(() => {
    const container = containerRef?.current || document;
    focusableElementsRef.current = getFocusableElements(container);
  }, [containerRef, getFocusableElements]);

  return {
    focusFirst,
    focusLast,
    focusNext,
    focusPrevious,
    focusByIndex,
    getFocusableElements: () => {
      const container = containerRef?.current || document;
      return getFocusableElements(container);
    },
    currentFocusIndex: currentFocusIndexRef.current
  };
};

export default useKeyboardNavigation;

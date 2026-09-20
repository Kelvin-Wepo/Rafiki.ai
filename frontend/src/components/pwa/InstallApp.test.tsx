import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { InstallAppButton } from './InstallApp';

vi.mock('../../hooks/usePwaInstall', () => ({
  usePwaInstall: () => ({
    isInstalled: false,
    canPrompt: true,
    showIosHelp: false,
    canShowButton: true,
    canShowBanner: true,
    install: vi.fn(),
    dismiss: vi.fn(),
  }),
}));

describe('InstallAppButton', () => {
  it('renders a one-tap install control when the app can be installed', () => {
    render(<InstallAppButton />);
    expect(screen.getByRole('button', { name: 'Install Rafiki on this device' })).toBeTruthy();
  });
});

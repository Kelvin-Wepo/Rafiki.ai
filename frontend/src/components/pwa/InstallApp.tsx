import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { Download, Share, X } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { usePwaInstall } from '../../hooks/usePwaInstall';
import './InstallApp.css';

function IosInstallSheet({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="pwa-sheet-backdrop" onClick={onClose}>
      <div
        className="pwa-sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <button
          ref={closeRef}
          type="button"
          className="pwa-sheet-close"
          onClick={onClose}
          aria-label="Close install instructions"
        >
          <X size={20} strokeWidth={1.75} aria-hidden="true" />
        </button>
        <h2 id={titleId} className="pwa-sheet-title">
          Add Rafiki to your Home Screen
        </h2>
        <p className="pwa-sheet-copy">
          iPhone and iPad install Rafiki from Safari&apos;s share menu — two taps, then it opens like any other app.
        </p>
        <ol className="pwa-sheet-steps">
          <li>
            Tap{' '}
            <span className="pwa-sheet-chip">
              <Share size={16} strokeWidth={2} aria-hidden="true" />
              Share
            </span>
          </li>
          <li>
            Scroll and tap <strong>Add to Home Screen</strong>
          </li>
          <li>
            Tap <strong>Add</strong>
          </li>
        </ol>
        <button type="button" className="pwa-sheet-done" onClick={onClose}>
          Got it
        </button>
      </div>
    </div>
  );
}

export function InstallAppButton({
  variant = 'header',
  className = '',
}: {
  variant?: 'header' | 'settings';
  className?: string;
}) {
  const { canShowButton, canPrompt, showIosHelp, install } = usePwaInstall();
  const [sheetOpen, setSheetOpen] = useState(false);

  const onClick = useCallback(async () => {
    if (canPrompt) {
      await install();
      return;
    }
    if (showIosHelp) setSheetOpen(true);
  }, [canPrompt, install, showIosHelp]);

  if (!canShowButton) return null;

  if (variant === 'settings') {
    return (
      <>
        <button type="button" className={`rd-btn-secondary ${className}`.trim()} onClick={onClick}>
          <Download size={16} strokeWidth={1.75} aria-hidden="true" />
          Install
        </button>
        <IosInstallSheet open={sheetOpen} onClose={() => setSheetOpen(false)} />
      </>
    );
  }

  return (
    <>
      <span className="rl-divider" aria-hidden="true" />
      <button
        type="button"
        className={`rl-control pwa-header-btn ${className}`.trim()}
        onClick={onClick}
        aria-label="Install Rafiki on this device"
      >
        <Download size={19} aria-hidden="true" />
        <span className="rl-control-label">Install</span>
      </button>
      <IosInstallSheet open={sheetOpen} onClose={() => setSheetOpen(false)} />
    </>
  );
}

export function InstallSettingsRow() {
  const { isInstalled, canShowButton, canPrompt, showIosHelp, install } = usePwaInstall();
  const [sheetOpen, setSheetOpen] = useState(false);

  const onClick = useCallback(async () => {
    if (canPrompt) {
      await install();
      return;
    }
    if (showIosHelp) setSheetOpen(true);
  }, [canPrompt, install, showIosHelp]);

  return (
    <div className="rd-setting">
      <span className="rd-setting-copy">
        <span className="rd-setting-name">Install app</span>
        <span className="rd-setting-desc">
          {isInstalled
            ? 'Rafiki is installed on this device'
            : canShowButton
              ? 'Add Rafiki to this device and open it in one tap'
              : 'In your browser menu, choose Install or Add to Home Screen'}
        </span>
      </span>
      {isInstalled ? (
        <span className="rd-setting-desc">Installed</span>
      ) : canShowButton ? (
        <button type="button" className="rd-btn-secondary" onClick={onClick}>
          <Download size={16} strokeWidth={1.75} aria-hidden="true" />
          Install
        </button>
      ) : null}
      <IosInstallSheet open={sheetOpen} onClose={() => setSheetOpen(false)} />
    </div>
  );
}

export function InstallBanner() {
  const location = useLocation();
  const { isAuthenticated, isVerifying } = useAuth();
  const { canShowBanner, canPrompt, showIosHelp, install, dismiss } = usePwaInstall();
  const [sheetOpen, setSheetOpen] = useState(false);
  const visible =
    canShowBanner &&
    !isAuthenticated &&
    !isVerifying &&
    !location.pathname.startsWith('/access');

  useEffect(() => {
    document.body.classList.toggle('pwa-banner-visible', visible);
    return () => document.body.classList.remove('pwa-banner-visible');
  }, [visible]);

  if (!visible) return null;

  const onInstall = async () => {
    if (canPrompt) {
      await install();
      return;
    }
    if (showIosHelp) setSheetOpen(true);
  };

  return (
    <>
      <div className="pwa-banner" role="region" aria-label="Install Rafiki">
        <div className="pwa-banner-copy">
          <strong className="pwa-banner-title">Install Rafiki</strong>
          <span className="pwa-banner-sub">Open it in one tap, like any other app on this device.</span>
        </div>
        <div className="pwa-banner-actions">
          <button type="button" className="pwa-banner-install" onClick={onInstall}>
            <Download size={18} strokeWidth={1.75} aria-hidden="true" />
            Install
          </button>
          <button type="button" className="pwa-banner-dismiss" onClick={dismiss}>
            Not now
          </button>
        </div>
      </div>
      <IosInstallSheet open={sheetOpen} onClose={() => setSheetOpen(false)} />
    </>
  );
}

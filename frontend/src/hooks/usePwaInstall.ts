import { useCallback, useEffect, useState } from 'react';
import {
  capturePwaInstallEvents,
  dismissPwaInstall,
  getPwaInstallState,
  promptPwaInstall,
  subscribePwaInstall,
  type PwaInstallOutcome,
} from '../lib/pwaInstall';

export type PwaInstallStatus = {
  isInstalled: boolean;
  canPrompt: boolean;
  showIosHelp: boolean;
  canShowButton: boolean;
  canShowBanner: boolean;
  install: () => Promise<PwaInstallOutcome>;
  dismiss: () => void;
};

/**
 * One-tap install state. Chromium (Android, desktop) exposes a native
 * prompt; iOS Safari does not, so we surface Add-to-Home-Screen help.
 */
export function usePwaInstall(): PwaInstallStatus {
  const [state, setState] = useState(() => {
    capturePwaInstallEvents();
    return getPwaInstallState();
  });

  useEffect(() => {
    capturePwaInstallEvents();
    setState(getPwaInstallState());
    return subscribePwaInstall(() => setState(getPwaInstallState()));
  }, []);

  const install = useCallback(() => promptPwaInstall(), []);
  const dismiss = useCallback(() => dismissPwaInstall(), []);

  const showIosHelp = state.isIos && !state.isInstalled;
  const canShowButton = (state.canPrompt || showIosHelp) && !state.isInstalled;

  return {
    isInstalled: state.isInstalled,
    canPrompt: state.canPrompt,
    showIosHelp,
    canShowButton,
    canShowBanner: canShowButton && !state.dismissed,
    install,
    dismiss,
  };
}

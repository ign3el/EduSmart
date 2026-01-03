/**
 * PWA Display Mode Hook
 * Detects if app is running in standalone mode (installed PWA)
 */

import { useState, useEffect } from 'react';

export function useDisplayMode() {
  const [displayMode, setDisplayMode] = useState('browser');
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Check if running as installed PWA
    const isStandaloneMode = 
      window.matchMedia('(display-mode: standalone)').matches ||
      window.navigator.standalone === true ||
      document.referrer.includes('android-app://');

    setIsStandalone(isStandaloneMode);
    setDisplayMode(isStandaloneMode ? 'standalone' : 'browser');

    // Listen for display mode changes
    const mediaQuery = window.matchMedia('(display-mode: standalone)');
    const handler = (e) => {
      setIsStandalone(e.matches);
      setDisplayMode(e.matches ? 'standalone' : 'browser');
      console.log(`Display mode changed: ${e.matches ? 'standalone' : 'browser'}`);
    };

    // Modern API
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handler);
      return () => mediaQuery.removeListener(handler);
    }
  }, []);

  return { displayMode, isStandalone };
}

/**
 * PWA Capabilities Hook
 * Returns various PWA-related capabilities and states
 */
export function usePWACapabilities() {
  const [capabilities, setCapabilities] = useState({
    canInstall: false,
    isInstalled: false,
    isOnline: navigator.onLine,
    hasServiceWorker: 'serviceWorker' in navigator,
    hasPushNotifications: 'PushManager' in window,
    hasBackgroundSync: 'sync' in (self.registration || {}),
    hasPersistentStorage: 'storage' in navigator && 'persist' in navigator.storage,
  });

  useEffect(() => {
    // Check if installed
    const checkInstalled = window.matchMedia('(display-mode: standalone)').matches;
    
    // Check if can install (install prompt available)
    const canInstall = typeof window.showInstallPrompt === 'function';

    setCapabilities(prev => ({
      ...prev,
      canInstall,
      isInstalled: checkInstalled,
    }));

    // Listen for online/offline
    const handleOnline = () => setCapabilities(prev => ({ ...prev, isOnline: true }));
    const handleOffline = () => setCapabilities(prev => ({ ...prev, isOnline: false }));

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return capabilities;
}

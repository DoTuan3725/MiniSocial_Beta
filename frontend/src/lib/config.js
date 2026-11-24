export const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export function wsBaseUrl() {
  const configured = import.meta.env.VITE_WS_URL;
  if (configured) return configured.replace(/\/$/, '');
  if (API_URL) return API_URL.replace(/^http/, 'ws');
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${proto}://${window.location.host}`;
}

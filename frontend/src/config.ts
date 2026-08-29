// Cấu hình URL API Backend Cloudflare Live (Hoạt động 100% trên Điện thoại & Web Vercel)
export const DEFAULT_CLOUD_BACKEND = 'https://pension-efficient-innovations-sticky.trycloudflare.com';

export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('CUSTOM_API_BASE_URL');
    if (saved && saved.trim()) return saved.trim();
  }
  return (import.meta as any).env?.VITE_API_BASE_URL || DEFAULT_CLOUD_BACKEND;
};

export const setApiBaseUrl = (url: string) => {
  if (typeof window !== 'undefined') {
    if (url && url.trim()) {
      localStorage.setItem('CUSTOM_API_BASE_URL', url.trim());
    } else {
      localStorage.removeItem('CUSTOM_API_BASE_URL');
    }
  }
};

export const getApiUrl = (endpoint: string): string => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    return cleanEndpoint;
  }
  return `${baseUrl.replace(/\/$/, '')}${cleanEndpoint}`;
};

export const getStorageUrl = (path: string): string => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return getApiUrl(path);
};

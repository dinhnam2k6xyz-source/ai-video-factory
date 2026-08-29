// Cấu hình URL API Backend (Tự động thích ứng Localhost hoặc Render Production)
export const API_BASE_URL: string = (import.meta as any).env?.VITE_API_BASE_URL || '';

export const getApiUrl = (endpoint: string): string => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  if (!API_BASE_URL) {
    return cleanEndpoint;
  }
  return `${API_BASE_URL.replace(/\/$/, '')}${cleanEndpoint}`;
};

export const getStorageUrl = (path: string): string => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return getApiUrl(path);
};

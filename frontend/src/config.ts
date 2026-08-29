// Cấu hình URL API Backend (Tự động chuyển đổi giữa Localhost và Cloud)
export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const isLocalhost = 
      hostname === 'localhost' || 
      hostname === '127.0.0.1' || 
      hostname === '0.0.0.0' ||
      hostname.startsWith('192.168.');

    // Nếu đang mở trên máy tính (localhost), luôn dùng relative endpoint để gọi trực tiếp Backend local
    if (isLocalhost) {
      return '';
    }

    // Nếu đang mở trên Vercel / Cloud, kiểm tra xem người dùng đã cấu hình URL Backend chưa
    const saved = localStorage.getItem('CUSTOM_API_BASE_URL');
    if (saved && saved.trim()) return saved.trim();
  }
  return (import.meta as any).env?.VITE_API_BASE_URL || '';
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

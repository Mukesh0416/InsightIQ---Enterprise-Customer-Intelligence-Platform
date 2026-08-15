import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios';
import toast from 'react-hot-toast';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export const tokenStorage = {
  getAccess: () => localStorage.getItem('iq_access_token'),
  getRefresh: () => localStorage.getItem('iq_refresh_token'),
  set: (access: string, refresh: string) => {
    localStorage.setItem('iq_access_token', access);
    localStorage.setItem('iq_refresh_token', refresh);
  },
  clear: () => {
    localStorage.removeItem('iq_access_token');
    localStorage.removeItem('iq_refresh_token');
  },
};

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
});

let isRefreshing = false;
let refreshQueue: Array<(token: string) => void> = [];

function processQueue(token: string) {
  refreshQueue.forEach((cb) => cb(token));
  refreshQueue = [];
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as AxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !original._retry) {
      const refreshToken = tokenStorage.getRefresh();
      if (!refreshToken) {
        tokenStorage.clear();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push((token) => {
            original.headers = { ...original.headers, Authorization: `Bearer ${token}` };
            resolve(apiClient(original));
          });
        });
      }

      original._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        tokenStorage.set(data.access_token, data.refresh_token ?? refreshToken);
        processQueue(data.access_token);
        original.headers = { ...original.headers, Authorization: `Bearer ${data.access_token}` };
        return apiClient(original);
      } catch {
        tokenStorage.clear();
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    if (error.response?.status === 403) {
      toast.error('You do not have permission to perform this action.');
    } else if (error.response?.status >= 500) {
      toast.error('A server error occurred. Please try again.');
    }

    return Promise.reject(error);
  },
);

export function createUploadClient(onProgress?: (pct: number) => void): AxiosInstance {
  const client = axios.create({ baseURL: BASE_URL, timeout: 300_000 });
  client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = tokenStorage.getAccess();
    if (token) config.headers.Authorization = `Bearer ${token}`;
    if (onProgress) {
      config.onUploadProgress = (e) => {
        if (e.total) onProgress(Math.round((e.loaded * 100) / e.total));
      };
    }
    return config;
  });
  return client;
}

export default apiClient;

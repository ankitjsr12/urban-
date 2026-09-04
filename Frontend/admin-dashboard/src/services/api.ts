import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosError } from 'axios';
import { useAuthStore } from '../stores/authStore';

const MOCK_MODE = import.meta.env.VITE_MOCK_MODE === 'true';
export { MOCK_MODE };

export const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
});

// Attach bearer token from store
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401 globally → logout
apiClient.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export function unwrap<T>(response: { data: { data: T } }): T {
  return response.data.data;
}

export async function get<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
  const res = await apiClient.get<{ data: T }>(path, config);
  return res.data.data;
}

export async function post<T>(path: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const res = await apiClient.post<{ data: T }>(path, body, config);
  return res.data.data;
}

export async function patch<T>(path: string, body?: unknown): Promise<T> {
  const res = await apiClient.patch<{ data: T }>(path, body);
  return res.data.data;
}

export async function del<T>(path: string): Promise<T> {
  const res = await apiClient.delete<{ data: T }>(path);
  return res.data.data;
}

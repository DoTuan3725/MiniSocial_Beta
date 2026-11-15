import axios from 'axios';
import { API_URL } from '../lib/config';
import { useAuth } from '../store/auth';

export const http = axios.create({ baseURL: `${API_URL}/api/v1`, withCredentials: true, timeout: 30000 });

http.interceptors.request.use((config) => {
  const token = useAuth.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing = null;

/** Gọi /auth/refresh (refresh token nằm trong HttpOnly Cookie). Gom các lời gọi đồng thời thành 1. */
export function refreshSession() {
  if (!refreshing) {
    refreshing = axios
      .post(`${API_URL}/api/v1/auth/refresh/`, null, { withCredentials: true })
      .then((r) => {
        const { access_token, user } = r.data.data;
        useAuth.getState().setSession(access_token, user);
        return access_token;
      })
      .catch((err) => {
        useAuth.getState().clear();
        throw err;
      })
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}

/** Access token hết hạn (401) -> tự refresh trong suốt rồi gửi lại request. */
http.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const isAuthCall = original?.url?.includes('/auth/');
    if (status === 401 && original && !original._retry && !isAuthCall && useAuth.getState().accessToken) {
      original._retry = true;
      try {
        const token = await refreshSession();
        original.headers.Authorization = `Bearer ${token}`;
        return http(original);
      } catch {
        if (window.location.pathname !== '/login') window.location.assign('/login');
      }
    }
    return Promise.reject(error);
  },
);

export const unwrap = (r) => r.data.data;

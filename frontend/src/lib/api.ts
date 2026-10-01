/**
 * Axios instance with the standard response envelope + JWT handling.
 *
 * - Requests carry the access token from localStorage.
 * - A 401 triggers a single refresh attempt against /api/auth/refresh/; on
 *   success the original request is retried, otherwise the session is cleared.
 */
import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

const ACCESS_KEY = "gym.access";
const REFRESH_KEY = "gym.refresh";

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(access: string, refresh?: string) {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export const api: AxiosInstance = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.access;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccess(): Promise<string | null> {
  const refresh = tokenStore.refresh;
  if (!refresh) return null;
  try {
    const { data } = await axios.post("/api/auth/refresh/", { refresh });
    const access = data?.data?.access as string | undefined;
    if (access) {
      tokenStore.set(access);
      return access;
    }
    return null;
  } catch {
    return null;
  }
}

api.interceptors.response.use(
  (resp) => resp,
  async (error) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retried?: boolean;
    };
    if (error.response?.status === 401 && original && !original._retried) {
      original._retried = true;
      refreshing = refreshing ?? refreshAccess();
      const newAccess = await refreshing;
      refreshing = null;
      if (newAccess) {
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      }
      tokenStore.clear();
    }
    return Promise.reject(error);
  },
);

/** Unwrap the `{ ok, data }` envelope, throwing on `{ ok: false }`. */
export async function unwrap<T>(promise: Promise<{ data: any }>): Promise<T> {
  const resp = await promise;
  const body = resp.data;
  if (body && body.ok === false) {
    throw new Error(body.error ?? "Request failed");
  }
  return body.data as T;
}

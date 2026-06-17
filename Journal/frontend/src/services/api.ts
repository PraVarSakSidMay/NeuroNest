/* ──────────────────────────────────────────────────────────────
   Axios API Client — Base Configuration
   ────────────────────────────────────────────────────────────── */
import axios from "axios";

/** Configured Axios instance pointing at the FastAPI backend */
const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // 60s — AI generation can take a while
});

/* ── Request Interceptor to add Authorization header ── */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("nn_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/* ── Response Interceptor ── */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server returned an error response
      const message =
        error.response.data?.detail ||
        error.response.data?.message ||
        "An unexpected error occurred";
      return Promise.reject(new Error(message));
    }
    if (error.request) {
      // No response received
      return Promise.reject(new Error("Unable to reach the server. Please check your connection."));
    }
    return Promise.reject(error);
  }
);

export default api;

import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api",
  timeout: 12_000,
  headers: { Accept: "application/json" },
});

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (error.code === "ECONNABORTED") return "The request timed out. Please try again.";
    if (!error.response) return "The CiteWise API is unavailable. Start the backend and retry.";
  }
  return "Something went wrong. Please try again.";
}

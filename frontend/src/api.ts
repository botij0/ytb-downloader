import axios from "axios";

export type HealthResponse = {
  status: "ok";
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse> {
  const response = await axios.get<HealthResponse>(`${API_BASE}/api/health`);
  return response.data;
}

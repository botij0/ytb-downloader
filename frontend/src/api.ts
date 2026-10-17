import axios from "axios";

export type HealthResponse = {
  status: "ok";
};

export type DownloadKind = "video" | "audio";

export type VideoQuality = "best" | "1080p" | "720p" | "480p";

export type DownloadJob = {
  id: string;
  url: string;
  kind: DownloadKind;
  status: "queued" | "downloading" | "done" | "failed";
  error: string | null;
  file_path: string | null;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse> {
  const response = await axios.get<HealthResponse>(`${API_BASE}/api/health`);
  return response.data;
}

export async function createDownload(
  url: string,
  kind: DownloadKind,
  quality: VideoQuality = "best",
): Promise<DownloadJob> {
  const response = await axios.post<DownloadJob>(`${API_BASE}/api/downloads`, {
    url,
    kind,
    quality,
  });
  return response.data;
}

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
  progress_percent: number | null;
};

export type VideoMetadata = {
  title: string;
  duration_secs: number;
  thumbnail_url: string;
  uploader: string;
};

// Empty by default: API calls go to the same origin that served the page.
// nginx (Docker) and the Vite dev server proxy /api to the backend, so this
// works from any host/IP without CORS or a baked-in localhost URL.
const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/+$/, "");

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

export async function getDownloads(): Promise<DownloadJob[]> {
  const response = await axios.get<DownloadJob[]>(`${API_BASE}/api/downloads`);
  return response.data;
}

export function getDownloadFileUrl(jobId: string): string {
  return `${API_BASE}/api/downloads/${jobId}/file`;
}

export async function getMetadata(url: string): Promise<VideoMetadata> {
  const response = await axios.get<VideoMetadata>(`${API_BASE}/api/metadata`, {
    params: { url },
  });
  return response.data;
}

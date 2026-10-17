import axios from "axios";
import { useEffect, useState } from "react";
import type {
  DownloadJob,
  DownloadKind,
  VideoMetadata,
  VideoQuality,
} from "./api";
import {
  createDownload,
  getDownloadFileUrl,
  getDownloads,
  getHealth,
  getMetadata,
} from "./api";

type ConnectionState = "checking" | "connected" | "disconnected";

export default function App() {
  const [connection, setConnection] = useState<ConnectionState>("checking");
  const [url, setUrl] = useState("");
  const [kind, setKind] = useState<DownloadKind>("video");
  const [quality, setQuality] = useState<VideoQuality>("best");
  const [job, setJob] = useState<DownloadJob | null>(null);
  const [jobs, setJobs] = useState<DownloadJob[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);

  useEffect(() => {
    getHealth().then(
      () => setConnection("connected"),
      () => setConnection("disconnected"),
    );
  }, []);

  useEffect(() => {
    getDownloads().then(setJobs, () => {});
  }, []);

  const hasActive = jobs.some(
    (item) => item.status === "queued" || item.status === "downloading",
  );

  useEffect(() => {
    if (!hasActive) {
      return;
    }
    const timer = window.setInterval(() => {
      getDownloads().then(setJobs, () => {});
    }, 2000);
    return () => window.clearInterval(timer);
  }, [hasActive]);

  async function handleUrlBlur() {
    if (url.trim() === "") {
      setMetadata(null);
      return;
    }
    try {
      const data = await getMetadata(url);
      if (data === null || data === undefined) {
        setMetadata(null);
        return;
      }
      setMetadata(data);
    } catch {
      setMetadata(null);
    }
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const created = await createDownload(url, kind, quality);
      setJob(created);
      try {
        setJobs(await getDownloads());
      } catch {
        setJobs((prev) => [created, ...prev]);
      }
    } catch (err) {
      setJob(null);
      if (axios.isAxiosError(err)) {
        const data = err.response?.data as { detail?: unknown } | undefined;
        if (data !== undefined && typeof data.detail === "string") {
          setError(data.detail);
        } else if (err.response === undefined) {
          setError("Could not reach the API. Is the backend running?");
        } else {
          setError("Download request failed.");
        }
      } else {
        setError("Download request failed.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main>
      <h1>ytb-downloader</h1>
      <p>This app will download YouTube video and audio.</p>
      <p>
        API:{" "}
        {connection === "connected"
          ? "connected"
          : connection === "checking"
            ? "checking..."
            : "disconnected"}
      </p>
      {metadata !== null && (
        <section>
          <h2>{metadata.title}</h2>
          <p>{metadata.uploader}</p>
          <p>{metadata.duration_secs}</p>
          <img src={metadata.thumbnail_url} alt={metadata.title} />
        </section>
      )}
      <form onSubmit={handleSubmit}>
        <label htmlFor="url">Video URL</label>
        <input
          id="url"
          type="text"
          placeholder="https://www.youtube.com/watch?v=..."
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          onBlur={() => {
            void handleUrlBlur();
          }}
        />
        <fieldset>
          <legend>Format</legend>
          <label>
            <input
              type="radio"
              name="kind"
              value="video"
              checked={kind === "video"}
              onChange={() => setKind("video")}
            />
            Video
          </label>
          <label>
            <input
              type="radio"
              name="kind"
              value="audio"
              checked={kind === "audio"}
              onChange={() => setKind("audio")}
            />
            Audio
          </label>
        </fieldset>
        <label htmlFor="quality">Quality</label>
        <select
          id="quality"
          value={quality}
          onChange={(event) => setQuality(event.target.value as VideoQuality)}
        >
          <option value="best">Best</option>
          <option value="1080p">1080p</option>
          <option value="720p">720p</option>
          <option value="480p">480p</option>
        </select>
        <button type="submit" disabled={submitting}>
          Download
        </button>
      </form>
      {error !== null && <p role="alert">{error}</p>}
      {job !== null && (
        <p>
          Job {job.id}: {job.status}
        </p>
      )}
      {jobs.length > 0 && (
        <section>
          <h2>Downloads</h2>
          <ul>
            {jobs.map((item) => (
              <li key={item.id}>
                <span>
                  Job {item.id}: {item.status}
                </span>{" "}
                <span>{item.progress_percent ?? 0}%</span>
                {item.error !== null && item.error !== "" && (
                  <span>{item.error}</span>
                )}
                {item.status === "done" && (
                  <a href={getDownloadFileUrl(item.id)} download>
                    Download file
                  </a>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}

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
import { LevelMeter, type MeterTone } from "./components/LevelMeter";

type ConnectionState = "checking" | "connected" | "disconnected";

const CONNECTION_TEXT: Record<ConnectionState, string> = {
  checking: "checking...",
  connected: "connected",
  disconnected: "disconnected",
};

const CONNECTION_LAMP: Record<ConnectionState, string> = {
  checking: "bg-[var(--amber)] motion-safe:animate-pulse",
  connected: "bg-[var(--mint)]",
  disconnected: "bg-[var(--ember)]",
};

const STATUS_TONE: Record<DownloadJob["status"], MeterTone> = {
  queued: "queued",
  downloading: "active",
  done: "done",
  failed: "failed",
};

function formatDuration(totalSeconds: number): string {
  const seconds = Math.max(0, Math.round(totalSeconds));
  const minutes = Math.floor((seconds % 3600) / 60);
  const rest = seconds % 60;
  const hours = Math.floor(seconds / 3600);
  const two = (value: number) => value.toString().padStart(2, "0");
  return hours > 0
    ? `${hours}:${two(minutes)}:${two(rest)}`
    : `${minutes}:${two(rest)}`;
}

export default function App() {
  const [connection, setConnection] = useState<ConnectionState>("checking");
  const [url, setUrl] = useState("");
  const [kind, setKind] = useState<DownloadKind>("video");
  const [quality, setQuality] = useState<VideoQuality>("best");
  const [job, setJob] = useState<DownloadJob | null>(null);
  const [jobs, setJobs] = useState<DownloadJob[]>([]);
  const [listLoaded, setListLoaded] = useState(false);
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
    getDownloads().then(
      (data) => {
        setJobs(data);
        setListLoaded(true);
      },
      () => {},
    );
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

  const hasReadout = error !== null || metadata !== null || job !== null;

  return (
    <main className="min-h-dvh px-4 py-8 sm:px-6 sm:py-14">
      <div className="mx-auto w-full max-w-3xl overflow-hidden rounded-[4px] border border-[var(--ink)]/80 bg-[var(--plate)] shadow-[inset_0_1px_0_rgba(255,255,255,0.85),0_1px_3px_rgba(25,29,27,0.16)]">
        {/* What you control: the faceplate, and the paste action as its hero. */}
        <div className="px-5 py-6 sm:px-7 sm:py-8">
          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
            <h1 className="type-plate text-xl leading-tight sm:text-2xl">
              ytb-downloader
            </h1>
            <p className="type-machine flex items-center gap-2 rounded-[3px] bg-[var(--glass)] px-3 py-1.5 text-xs text-[var(--frost)]">
              <span
                aria-hidden="true"
                className={`size-2 shrink-0 rounded-full ${CONNECTION_LAMP[connection]}`}
              />
              API: {CONNECTION_TEXT[connection]}
            </p>
          </div>
          <p className="mt-1 text-sm text-[var(--steel)]">
            Paste a YouTube link, choose a format, keep the file.
          </p>

          <form className="mt-6 flex flex-col gap-5" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="url"
                className="text-xs font-medium text-[var(--steel)]"
              >
                Video URL
              </label>
              <input
                id="url"
                type="text"
                className="w-full rounded-[3px] border border-[var(--ink)]/25 bg-white/75 px-3.5 py-3 text-base shadow-[inset_0_1px_2px_rgba(25,29,27,0.12)] placeholder:text-[var(--steel)] hover:border-[var(--ink)]/40 focus:border-[var(--ink)]/60"
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                onBlur={() => {
                  void handleUrlBlur();
                }}
              />
            </div>

            <div className="flex flex-col gap-5 sm:flex-row sm:flex-wrap sm:items-end sm:gap-x-8">
              <fieldset className="min-w-0">
                <legend className="text-xs font-medium text-[var(--steel)]">
                  Format
                </legend>
                <div className="mt-1.5 flex rounded-[3px] border border-[var(--ink)]/25 p-0.5">
                  <label className="flex cursor-pointer items-center gap-2 rounded-[2px] px-3 py-2 text-sm has-[:checked]:bg-[var(--ink)] has-[:checked]:text-[var(--plate)]">
                    <input
                      type="radio"
                      name="kind"
                      value="video"
                      checked={kind === "video"}
                      onChange={() => setKind("video")}
                      className="size-3.5 shrink-0 appearance-none rounded-full border border-[var(--ink)]/50 checked:border-[var(--amber)] checked:bg-[var(--amber)]"
                    />
                    Video
                  </label>
                  <label className="flex cursor-pointer items-center gap-2 rounded-[2px] px-3 py-2 text-sm has-[:checked]:bg-[var(--ink)] has-[:checked]:text-[var(--plate)]">
                    <input
                      type="radio"
                      name="kind"
                      value="audio"
                      checked={kind === "audio"}
                      onChange={() => setKind("audio")}
                      className="size-3.5 shrink-0 appearance-none rounded-full border border-[var(--ink)]/50 checked:border-[var(--amber)] checked:bg-[var(--amber)]"
                    />
                    Audio
                  </label>
                </div>
              </fieldset>

              <div className="flex flex-col gap-1.5">
                <label
                  htmlFor="quality"
                  className="text-xs font-medium text-[var(--steel)]"
                >
                  Quality
                </label>
                <div className="relative">
                  <select
                    id="quality"
                    className="type-machine w-full appearance-none rounded-[3px] border border-[var(--ink)]/25 bg-white/75 py-2 pr-9 pl-3 text-sm hover:border-[var(--ink)]/40 sm:w-32"
                    value={quality}
                    onChange={(event) =>
                      setQuality(event.target.value as VideoQuality)
                    }
                  >
                    <option value="best">Best</option>
                    <option value="1080p">1080p</option>
                    <option value="720p">720p</option>
                    <option value="480p">480p</option>
                  </select>
                  <span
                    aria-hidden="true"
                    className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-xs text-[var(--ink)]/60"
                  >
                    ▾
                  </span>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-[3px] border border-[var(--ink)] bg-[var(--amber)] px-7 py-3 text-sm font-semibold text-[var(--ink)] transition-colors hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60 sm:ml-auto sm:w-auto"
              >
                Download
              </button>
            </div>
          </form>
        </div>

        {/* What the machine reports: dial glass, full bleed. */}
        <section className="flex flex-col gap-4 border-t border-[var(--ink)] bg-[var(--glass)] px-5 py-5 text-[var(--frost)] shadow-[inset_0_1px_0_rgba(230,233,228,0.07)] sm:px-7 sm:py-6">
          {error !== null && (
            <p
              role="alert"
              className="readout-in flex items-start gap-2 rounded-[3px] bg-[var(--ember)]/15 px-3 py-2 text-sm text-[var(--ember)]"
            >
              <span
                aria-hidden="true"
                className="mt-1.5 size-1.5 shrink-0 rounded-full bg-[var(--ember)]"
              />
              {error}
            </p>
          )}

          {metadata !== null && (
            <div className="readout-in flex flex-wrap items-start gap-x-4 gap-y-3">
              <img
                src={metadata.thumbnail_url}
                alt={metadata.title}
                className="h-[54px] w-24 shrink-0 rounded-[2px] object-cover ring-1 ring-[var(--frost)]/20"
              />
              <div className="min-w-0 flex-1">
                <h2 className="type-plate text-lg leading-snug text-[var(--frost)]">
                  {metadata.title}
                </h2>
                <dl className="mt-2 flex flex-wrap gap-x-8 gap-y-2">
                  <div>
                    <dt className="text-xs text-[var(--frost)]/50">uploader</dt>
                    <dd className="type-machine text-sm text-[var(--frost)]/90">
                      {metadata.uploader}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-[var(--frost)]/50">length</dt>
                    <dd className="type-machine text-sm text-[var(--frost)]/90">
                      {formatDuration(metadata.duration_secs)}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          )}

          {job !== null && (
            <p className="readout-in type-machine flex items-center gap-2 text-sm text-[var(--frost)]/90">
              <span
                aria-hidden="true"
                className="size-1.5 shrink-0 rounded-full bg-[var(--amber)]"
              />
              Job {job.id}: {job.status}
            </p>
          )}

          <div
            className={
              hasReadout ? "border-t border-[var(--frost)]/10 pt-4" : undefined
            }
          >
            <h2 className="text-sm font-medium text-[var(--frost)]/70">
              Queue
            </h2>
            {jobs.length > 0 ? (
              <ul className="mt-1">
                {jobs.map((item) => (
                  <li
                    key={item.id}
                    className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-[var(--frost)]/10 py-3 last:border-b-0"
                  >
                    <span className="type-machine w-full min-w-0 text-sm text-[var(--frost)]/90 sm:w-auto sm:flex-1 sm:truncate">
                      Job {item.id}: {item.status}
                    </span>
                    <LevelMeter
                      percent={item.progress_percent ?? 0}
                      tone={STATUS_TONE[item.status]}
                      label={`Progress for job ${item.id}`}
                      className="flex-1 sm:w-28 sm:flex-none"
                    />
                    <span className="type-machine ml-auto w-11 shrink-0 text-right text-xs text-[var(--frost)]/60 sm:ml-0">
                      {item.progress_percent ?? 0}%
                    </span>
                    {item.status === "done" && (
                      <a
                        href={getDownloadFileUrl(item.id)}
                        download
                        className="rounded-[2px] text-sm font-medium text-[var(--amber)] underline-offset-4 hover:underline focus-visible:outline-[var(--amber)]"
                      >
                        Download file
                      </a>
                    )}
                    {item.error !== null && item.error !== "" && (
                      <span className="w-full text-sm text-[var(--ember)]">
                        {item.error}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            ) : listLoaded ? (
              <p className="mt-2 text-sm text-[var(--frost)]/60">
                Nothing queued yet. Paste a link above to start.
              </p>
            ) : null}
          </div>
        </section>
      </div>
    </main>
  );
}

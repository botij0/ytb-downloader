import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import type { DownloadJob, VideoMetadata } from "./api";
import { createDownload, getDownloads, getHealth, getMetadata } from "./api";

vi.mock("./api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./api")>();
  return {
    ...actual,
    getHealth: vi.fn(),
    createDownload: vi.fn(),
    getDownloads: vi.fn(),
    getMetadata: vi.fn(),
  };
});

const mockGetHealth = vi.mocked(getHealth);
const mockCreateDownload = vi.mocked(createDownload);
const mockGetDownloads = vi.mocked(getDownloads);
const mockGetMetadata = vi.mocked(getMetadata);

const queuedJob: DownloadJob = {
  id: "abc123",
  url: "https://www.youtube.com/watch?v=abc123",
  kind: "video",
  status: "queued",
  error: null,
  file_path: null,
  progress_percent: null,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

beforeEach(() => {
  mockGetHealth.mockResolvedValue({ status: "ok" });
  mockCreateDownload.mockResolvedValue(queuedJob);
  mockGetDownloads.mockResolvedValue([]);
  mockGetMetadata.mockResolvedValue(null as unknown as VideoMetadata);
});

describe("health status", () => {
  it("shows connected when the health check resolves", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/api:\s*connected/i)).toBeTruthy();
    });
  });

  it("shows disconnected when the health check rejects", async () => {
    mockGetHealth.mockRejectedValueOnce(new Error("offline"));
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/api:\s*disconnected/i)).toBeTruthy();
    });
  });
});

describe("download form", () => {
  it("submits the entered URL and shows the queued job line", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(
      screen.getByLabelText(/video url/i),
      "https://www.youtube.com/watch?v=abc123",
    );
    await user.click(screen.getByRole("button", { name: /download/i }));

    await waitFor(() => {
      expect(mockCreateDownload).toHaveBeenCalledWith(
        "https://www.youtube.com/watch?v=abc123",
        "video",
        "best",
      );
    });
    expect(await screen.findByText("Job abc123: queued")).toBeTruthy();
  });

  it("passes the selected format to the download request", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(
      screen.getByLabelText(/video url/i),
      "https://www.youtube.com/watch?v=abc123",
    );
    await user.click(screen.getByRole("radio", { name: /audio/i }));
    await user.click(screen.getByRole("button", { name: /download/i }));

    await waitFor(() => {
      expect(mockCreateDownload).toHaveBeenCalledWith(
        "https://www.youtube.com/watch?v=abc123",
        "audio",
        "best",
      );
    });
  });

  it("shows the error line when the submit is rejected", async () => {
    mockCreateDownload.mockRejectedValueOnce(new Error("boom"));
    const user = userEvent.setup();
    render(<App />);

    await user.type(
      screen.getByLabelText(/video url/i),
      "https://www.youtube.com/watch?v=abc123",
    );
    await user.click(screen.getByRole("button", { name: /download/i }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toMatch(/Download request failed\./);
    expect(screen.queryByText(/job abc123:/i)).toBeNull();
  });
});

describe("video metadata", () => {
  const canned: VideoMetadata = {
    title: "Never Gonna Give You Up",
    duration_secs: 212,
    thumbnail_url: "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
    uploader: "Rick Astley",
  };

  it("shows the metadata block when the URL field loses focus", async () => {
    mockGetMetadata.mockResolvedValueOnce(canned);
    const user = userEvent.setup();
    render(<App />);

    await user.type(
      screen.getByLabelText(/video url/i),
      "https://www.youtube.com/watch?v=abc123",
    );
    fireEvent.blur(screen.getByLabelText(/video url/i));

    expect(await screen.findByText("Never Gonna Give You Up")).toBeTruthy();
    expect(screen.getByText("Rick Astley")).toBeTruthy();
  });

  it("shows no metadata block when the lookup resolves empty", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(
      screen.getByLabelText(/video url/i),
      "https://www.youtube.com/watch?v=abc123",
    );
    fireEvent.blur(screen.getByLabelText(/video url/i));

    await waitFor(() => {
      expect(mockGetMetadata).toHaveBeenCalled();
    });
    expect(screen.queryByText("Never Gonna Give You Up")).toBeNull();
  });
});

describe("download list", () => {
  const doneJob: DownloadJob = {
    id: "done1",
    url: "https://www.youtube.com/watch?v=done1",
    kind: "video",
    status: "done",
    error: null,
    file_path: "/tmp/done1.mp4",
    progress_percent: 100,
  };

  const failedJob: DownloadJob = {
    id: "fail1",
    url: "https://www.youtube.com/watch?v=fail1",
    kind: "video",
    status: "failed",
    error: "boom went wrong",
    file_path: null,
    progress_percent: 42,
  };

  it("renders rows for fetched jobs", async () => {
    mockGetDownloads.mockResolvedValue([doneJob, failedJob]);
    render(<App />);

    expect(await screen.findByText(/Job done1: done/)).toBeTruthy();
    expect(await screen.findByText(/Job fail1: failed/)).toBeTruthy();
  });

  it("renders a download link for done jobs", async () => {
    mockGetDownloads.mockResolvedValue([doneJob]);
    render(<App />);

    const link = await screen.findByRole("link", { name: /download file/i });
    expect(link.getAttribute("href")).toContain("/api/downloads/done1/file");
    expect(link.hasAttribute("download")).toBe(true);
  });

  it("shows the error for failed jobs", async () => {
    mockGetDownloads.mockResolvedValue([failedJob]);
    render(<App />);

    expect(await screen.findByText("boom went wrong")).toBeTruthy();
  });
});

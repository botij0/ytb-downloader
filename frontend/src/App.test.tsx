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
import { createDownload, getHealth, getMetadata } from "./api";

vi.mock("./api");

const mockGetHealth = vi.mocked(getHealth);
const mockCreateDownload = vi.mocked(createDownload);
const mockGetMetadata = vi.mocked(getMetadata);

const queuedJob: DownloadJob = {
  id: "abc123",
  url: "https://www.youtube.com/watch?v=abc123",
  kind: "video",
  status: "queued",
  error: null,
  file_path: null,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

beforeEach(() => {
  mockGetHealth.mockResolvedValue({ status: "ok" });
  mockCreateDownload.mockResolvedValue(queuedJob);
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

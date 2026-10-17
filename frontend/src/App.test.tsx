import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import type { DownloadJob } from "./api";
import { createDownload, getHealth } from "./api";

vi.mock("./api");

const mockGetHealth = vi.mocked(getHealth);
const mockCreateDownload = vi.mocked(createDownload);

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

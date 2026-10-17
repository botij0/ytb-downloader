import { useEffect, useState } from "react";
import { getHealth } from "./api";

type ConnectionState = "checking" | "connected" | "disconnected";

export default function App() {
  const [connection, setConnection] = useState<ConnectionState>("checking");

  useEffect(() => {
    getHealth().then(
      () => setConnection("connected"),
      () => setConnection("disconnected"),
    );
  }, []);

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
      <label htmlFor="url">Video URL</label>
      <input
        id="url"
        type="text"
        placeholder="https://www.youtube.com/watch?v=..."
        disabled
      />
    </main>
  );
}

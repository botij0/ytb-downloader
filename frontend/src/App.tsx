export default function App() {
  return (
    <main>
      <h1>ytb-downloader</h1>
      <p>This app will download YouTube video and audio.</p>
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

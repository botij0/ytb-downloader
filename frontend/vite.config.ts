import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Keep dev requests same-origin; nginx does the same in Docker.
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});

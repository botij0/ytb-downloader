# ytb-downloader

Paste a YouTube URL, preview its metadata, pick video or audio plus quality, then create a download job and fetch the finished file. The backend is FastAPI plus yt-dlp. The frontend is React plus Vite and shows backend health in the header.

## Prerequisites

- `uv` and Python 3.12 or newer. `backend/pyproject.toml` sets `requires-python = ">=3.12"`.
- Node 20 or newer and `npm` for the Vite frontend.

## Backend (dev run)

```sh
cd backend
uv run uvicorn app.main:app --reload
```

The API listens on `http://localhost:8000`. That host and port are the uvicorn defaults. Check health with `curl http://localhost:8000/api/health`. A healthy server returns `{"status": "ok"}` from `GET /api/health` in `backend/app/main.py`.

## Frontend (dev run)

```sh
cd frontend
npm install
npm run dev
```

Vite serves the app on `http://localhost:5173`. That origin is listed in the backend CORS allow list in `backend/app/main.py`, so keep both servers running. The header reads `connected` when `GET /api/health` succeeds.

## Configuration

Set `YTB_DOWNLOAD_DIR` to choose where finished downloads are stored. It defaults to `./downloads` relative to the working directory that starts the server.

| Variable | Used by | Default |
| --- | --- | --- |
| `YTB_DOWNLOAD_DIR` | Backend (`backend/app/engine.py`) | `./downloads`, relative to the working directory that starts the server |
| `VITE_API_BASE` | Frontend (`frontend/src/api.ts`) | `http://localhost:8000` |

Example:

```sh
YTB_DOWNLOAD_DIR=/tmp/ytb-downloads uv run uvicorn app.main:app --reload
VITE_API_BASE=http://localhost:8000 npm run dev
```

Run the frontend example from `frontend/`. Run the backend example from `backend/`.

## Checks

Run lint from the repo root:

```sh
npm run lint
```

That script in `package.json` runs the frontend Biome check and the backend Ruff check plus format check.

Backend tests:

```sh
cd backend
uv run pytest
```

Frontend tests:

```sh
cd frontend
npm test
```

That script in `frontend/package.json` runs `vitest run`.

Frontend build:

```sh
cd frontend
npm run build
```

That script in `frontend/package.json` runs `tsc --noEmit && vite build`.

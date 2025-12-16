# Voice assist

Lightweight backend for a WebRTC voice assistant demo. It accepts microphone audio from the browser, runs STT, sends the transcript to OpenAI for a short reply, and streams TTS audio back to the client.

## Quick start (development)

1. Make the helper script executable and run it:

```bash
chmod +x scripts/run_https.sh
./scripts/run_https.sh
```

2. Open the frontend in your browser:

- `https://localhost:8000/` or
- `https://<wsl-ip>:8000/` (replace `<wsl-ip>` with the address from `hostname -I` when running in WSL)

Accept the self-signed certificate warning in your browser (development only).

## What it does

- Captures microphone audio from the browser via WebRTC.
- Transcribes audio using the STT model from `fastrtc`.
- Sends the transcript to OpenAI chat completions for a short reply.
- Synthesizes the reply to audio using the TTS model from `fastrtc` and streams it back to the browser.

## Tech stack

- Python 3.11+
- FastAPI
- fastrtc (WebRTC, STT, TTS helpers)
- openai (chat completions)
- uvicorn (ASGI server)

## Project layout

- `main.py` — app entry, mounts `fastrtc.Stream`, serves `/` and static files
- `static/` — frontend files (`index.html`, `client.js`)
- `scripts/run_https.sh` — helper script to generate a self-signed cert and run uvicorn with TLS

## Endpoints

- `GET /` — frontend
- `POST /webrtc/offer` — endpoint used by the frontend to send an SDP offer (handled by `fastrtc`)

## Troubleshooting

- If `navigator.mediaDevices.getUserMedia` is undefined, make sure you're on `https://` or `http://localhost`.
- When running in WSL2, prefer either the provided HTTPS script or create a Windows port proxy to forward `localhost:8000` to the WSL IP.
- Server logs include basic audio diagnostics in `main.py` to help debug incoming audio shapes.

## Notes

- This project is intended for local development only. The self-signed certificate is insecure and not for production.
- No `requirements.txt` is included by design — manage dependencies in your preferred way.

If you'd like a `requirements.txt`, Dockerfile, or additional developer notes, I can add them.

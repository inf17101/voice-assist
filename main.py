import logging
from typing import Any

from fastrtc import (ReplyOnPause, Stream, get_stt_model, get_tts_model)
from openai import OpenAI
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import numpy as np
except Exception:
    np = None

client = OpenAI()
stt_model = get_stt_model()
tts_model = get_tts_model()

def run_assistant(audio: tuple[int, np.ndarray]):
    if audio:
        sample_rate, audio_data = audio
        logger.debug(f"Received audio chunk with sample rate: {sample_rate}, length: {audio_data.shape}")

    prompt = stt_model.stt(audio)
    completion = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant. You reply optimized for text-to-speech synthesis without special characters than '.', '!' or '?'. You keep your replies concise and friendly."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=200,
    )
    reply = completion.choices[0].message.content
    for audio_chunk in tts_model.stream_tts_sync(reply):
        yield audio_chunk

stream = Stream(ReplyOnPause(run_assistant), modality="audio", mode="send-receive")

app = FastAPI()
stream.mount(app)

# Mount the 'static' directory at /static to serve JS/CSS/assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at the root path so visiting '/' loads the frontend page
ROOT = Path(__file__).parent / "static" / "index.html"


@app.get("/")
def root():
    return FileResponse(ROOT)

# uvicorn main:app --host 0.0.0.0 --port 8000

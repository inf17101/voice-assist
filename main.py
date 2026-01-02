import logging
from dotenv import load_dotenv

from fastrtc import (ReplyOnStopWords, Stream, get_stt_model, get_tts_model)
from openai import OpenAI
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from humaware_vad import HumAwareVADModel

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import numpy as np
except Exception:
    np = None

client = OpenAI()
stt_model = get_stt_model()
tts_model = get_tts_model()
vad_model = HumAwareVADModel()

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
    stream=True,
    )

    buffer = ""
    for chunk in completion:
        text_part = str(chunk.choices[0].delta.content)
        buffer += text_part
        if any(text_part.endswith(c) for c in (".", "!", "?")):
            for audio_chunk in tts_model.stream_tts_sync(buffer):
                yield audio_chunk
            buffer = ""

stream = Stream(ReplyOnStopWords(run_assistant, model=vad_model, stop_words=["Buddy"]), modality="audio", mode="send-receive")

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

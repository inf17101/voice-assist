import logging
from dotenv import load_dotenv

from fastrtc import (ReplyOnStopWords, Stream, get_stt_model, get_tts_model)
from agents import Runner, Agent, ModelSettings, SQLiteSession, WebSearchTool
from agents.mcp import MCPServerStreamableHttp
from agents.extensions.memory import EncryptedSession
from openai.types.responses import ResponseTextDeltaEvent
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os
from humaware_vad import HumAwareVADModel

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import numpy as np
except Exception:
    np = None

stt_model = get_stt_model()
tts_model = get_tts_model()
vad_model = HumAwareVADModel()

# Create encrypted SQLite session
underlying = SQLiteSession("user-1")

session = EncryptedSession(
    session_id="user-1",
    underlying_session=underlying,
    encryption_key="secret-key",
    ttl=120,
)

homeassistant_mcp = MCPServerStreamableHttp(
        name="Home Assistant",
        params={
            "url": "http://homeassistant.local:8123/api/mcp",
            "headers": {"Authorization": f"Bearer {os.getenv("HA_TOKEN", "")}"},
            "timeout": 10,
        },
        cache_tools_list=True,
        max_retry_attempts=10,
    )

async def run_assistant(audio: tuple[int, np.ndarray]):
    logger.info(f"audio: {audio}")
    if audio:
        sample_rate, audio_data = audio
        logger.info(f"Received audio chunk with sample rate: {sample_rate}, length: {audio_data.shape}")

    try:
        prompt = stt_model.stt(audio)

        async with homeassistant_mcp as server:
            assistant = Agent(
                name="Home Assistant",
                instructions="You are a helpful assistant. You reply optimized for text-to-speech synthesis without special characters other than '.', '!' or '?'. You keep your replies concise and friendly. Do not format output in headlines or markdown. Do not output internet links.",
                model_settings=ModelSettings(max_tokens=200),
                model="gpt-4.1-mini",
                mcp_servers=[server],
                tools=[WebSearchTool()]
            )

            buffer = ""
            result = Runner.run_streamed(assistant, input=prompt, session=session)
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    chunk = event.data.delta
                    buffer += chunk
                    if any(chunk.endswith(c) for c in (".", "!", "?")):
                        logger.debug(f"Agent sentence: '{buffer}'")
                        async for audio_chunk in tts_model.stream_tts(buffer):
                            yield audio_chunk
                        buffer = ""

    except Exception as e:
        error_reply = "Error processing request."
        logger.error(e)
        async for audio_chunk in tts_model.stream_tts(error_reply):
            yield audio_chunk

stream = Stream(ReplyOnStopWords(run_assistant, model=vad_model, stop_words=["Buddy"], input_sample_rate=16000), modality="audio", mode="send-receive")

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

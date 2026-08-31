"""Text-to-speech providers."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 4096


class TextToSpeechError(Exception):
    """Raised when synthesis fails."""


class LocalTTS:
    """Text-to-speech using pyttsx3 (offline, system voices)."""

    def __init__(self, rate: int = 150, volume: float = 1.0) -> None:
        self.rate = rate
        self.volume = volume
        self._engine: Any | None = None

    def _get_engine(self) -> Any:
        if self._engine is None:
            try:
                import pyttsx3
            except ImportError as exc:
                raise TextToSpeechError("pyttsx3 is not installed") from exc
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            self._engine = engine
        return self._engine

    async def speak(self, text: str) -> bytes:
        """Convert text to WAV audio bytes."""
        if not text.strip():
            raise TextToSpeechError("Empty text")

        temp_path: Path | None = None

        def _run() -> bytes:
            nonlocal temp_path
            engine = self._get_engine()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
                temp_path = Path(handle.name)
            engine.save_to_file(text, str(temp_path))
            engine.runAndWait()
            data = temp_path.read_bytes()
            if not data:
                raise TextToSpeechError("TTS produced empty audio")
            return data

        try:
            return await asyncio.to_thread(_run)
        except TextToSpeechError:
            raise
        except Exception as exc:
            logger.exception("Local TTS synthesis failed")
            raise TextToSpeechError("Local TTS synthesis failed") from exc
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    async def speak_stream(
        self,
        text: str,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesized audio in fixed-size chunks."""
        audio_bytes = await self.speak(text)
        for index in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[index : index + chunk_size]


class DeterministicTTS:
    """Lightweight TTS for tests without pyttsx3."""

    def __init__(self, payload: bytes | None = None) -> None:
        self.payload = payload or b"RIFF....fake-wav"

    async def speak(self, text: str) -> bytes:
        if not text.strip():
            raise TextToSpeechError("Empty text")
        return self.payload

    async def speak_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        data = await self.speak(text)
        yield data

"""Speech-to-text providers."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SpeechToTextError(Exception):
    """Raised when transcription fails."""


class WhisperSTT:
    """Speech-to-text using OpenAI Whisper."""

    def __init__(self, model_name: str = "base") -> None:
        self.model_name = model_name
        self._model: Any | None = None

    def _get_model(self) -> Any:
        if self._model is None:
            try:
                import whisper
            except ImportError as exc:
                raise SpeechToTextError(
                    "openai-whisper is not installed"
                ) from exc
            self._model = whisper.load_model(self.model_name)
        return self._model

    async def transcribe(self, audio_file: Path, language: str = "it") -> str:
        """Transcribe an audio file (WAV, MP3, etc.)."""
        if not audio_file.is_file():
            raise SpeechToTextError(f"Audio file not found: {audio_file}")

        def _run() -> str:
            result = self._get_model().transcribe(str(audio_file), language=language)
            text = str(result.get("text", "")).strip()
            if not text:
                raise SpeechToTextError("Empty transcription result")
            return text

        try:
            return await asyncio.to_thread(_run)
        except SpeechToTextError:
            raise
        except Exception as exc:
            logger.exception("Whisper transcription failed")
            raise SpeechToTextError("Whisper transcription failed") from exc

    async def transcribe_stream(self, audio_bytes: bytes) -> str:
        """Transcribe raw audio bytes via a temporary WAV file."""
        if not audio_bytes:
            raise SpeechToTextError("Empty audio payload")

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
                handle.write(audio_bytes)
                handle.flush()
                temp_path = Path(handle.name)
            return await self.transcribe(temp_path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    async def transcribe_stream_chunks(
        self,
        chunks: AsyncGenerator[bytes, None],
    ) -> str:
        """Collect streamed audio chunks and transcribe the full buffer."""
        buffer = bytearray()
        async for chunk in chunks:
            buffer.extend(chunk)
        return await self.transcribe_stream(bytes(buffer))


class DeterministicSTT:
    """Lightweight STT for tests and offline development without Whisper."""

    def __init__(self, default_text: str = "ciao laboratorio") -> None:
        self.default_text = default_text

    async def transcribe(self, audio_file: Path, language: str = "it") -> str:
        _ = language
        if not audio_file.is_file():
            raise SpeechToTextError(f"Audio file not found: {audio_file}")
        return self.default_text

    async def transcribe_stream(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            raise SpeechToTextError("Empty audio payload")
        return self.default_text

"""Sync adapters bridging legacy voice interfaces to async STT/TTS providers."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, TypeVar

from app.voice.interfaces import SpeechToText, TextToSpeech, TranscriptResult, VoiceInput

T = TypeVar("T")


def voice_input_to_bytes(voice_input: VoiceInput) -> bytes:
    """Resolve captured audio reference to raw bytes for async STT."""
    ref = voice_input.audio_reference.strip()
    if not ref:
        return b"\x00"
    path = Path(ref)
    if path.is_file():
        return path.read_bytes()
    return ref.encode("utf-8")


def run_async(coro: Any) -> Any:
    """Run an async coroutine from sync code (safe if a loop is already running)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


class SyncSTTAdapter(SpeechToText):
    """Wrap async STT (WhisperSTT, DeterministicSTT) for the sync conversation engine."""

    def __init__(self, stt: Any) -> None:
        self._stt = stt

    def transcribe(self, voice_input: VoiceInput) -> TranscriptResult:
        audio_bytes = voice_input_to_bytes(voice_input)
        text = run_async(self._stt.transcribe_stream(audio_bytes))
        return TranscriptResult(text=text, confidence=0.95, is_final=True)


class SyncTTSAdapter(TextToSpeech):
    """Wrap async TTS (LocalTTS, DeterministicTTS) for the sync conversation engine."""

    def __init__(self, tts: Any) -> None:
        self._tts = tts

    def synthesize(self, text: str) -> VoiceInput:
        audio_bytes = run_async(self._tts.speak(text))
        return VoiceInput(
            audio_reference=f"tts:{len(audio_bytes)}",
            duration_ms=None,
        )


def default_sync_stt() -> SyncSTTAdapter:
    from app.voice.speech_to_text import DeterministicSTT

    return SyncSTTAdapter(DeterministicSTT())


def default_sync_tts() -> SyncTTSAdapter:
    from app.voice.text_to_speech import DeterministicTTS

    return SyncTTSAdapter(DeterministicTTS())

"""Voice input/output abstractions (mock only in this phase)."""

from abc import ABC, abstractmethod
from collections.abc import Iterator

from pydantic import BaseModel


class VoiceInput(BaseModel):
    """Captured voice input reference."""

    audio_reference: str
    duration_ms: int | None = None


class TranscriptResult(BaseModel):
    """Speech-to-text output."""

    text: str
    confidence: float = 1.0
    is_final: bool = True


class SpeechToText(ABC):
    """Abstract speech-to-text provider."""

    @abstractmethod
    def transcribe(self, voice_input: VoiceInput) -> TranscriptResult:
        raise NotImplementedError


class TextToSpeech(ABC):
    """Abstract text-to-speech provider."""

    @abstractmethod
    def synthesize(self, text: str) -> VoiceInput:
        raise NotImplementedError


class MockSpeechToText(SpeechToText):
    """Mock STT returning deterministic transcript text."""

    def transcribe(self, voice_input: VoiceInput) -> TranscriptResult:
        return TranscriptResult(
            text=f"[MOCK STT] transcript for {voice_input.audio_reference}",
            confidence=0.95,
        )


class MockTextToSpeech(TextToSpeech):
    """Mock TTS returning a placeholder audio reference."""

    def synthesize(self, text: str) -> VoiceInput:
        return VoiceInput(audio_reference=f"mock-tts:{hash(text) & 0xFFFF}")

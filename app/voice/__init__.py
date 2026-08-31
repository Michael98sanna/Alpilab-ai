"""Voice abstractions for Alpilab AI."""

from app.voice.interfaces import (
    MockSpeechToText,
    MockTextToSpeech,
    SpeechToText,
    TextToSpeech,
    TranscriptResult,
    VoiceInput,
)
from app.voice.speech_to_text import DeterministicSTT, SpeechToTextError, WhisperSTT
from app.voice.sync_adapters import (
    SyncSTTAdapter,
    SyncTTSAdapter,
    default_sync_stt,
    default_sync_tts,
)
from app.voice.text_to_speech import DeterministicTTS, LocalTTS, TextToSpeechError

__all__ = [
    "DeterministicSTT",
    "DeterministicTTS",
    "LocalTTS",
    "MockSpeechToText",
    "MockTextToSpeech",
    "SpeechToText",
    "SpeechToTextError",
    "SyncSTTAdapter",
    "SyncTTSAdapter",
    "TextToSpeech",
    "TextToSpeechError",
    "TranscriptResult",
    "VoiceInput",
    "WhisperSTT",
    "default_sync_stt",
    "default_sync_tts",
]

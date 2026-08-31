"""Tests for voice STT/TTS (Priority 8)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.conversation.command_engine import ConversationCommandEngine
from app.schemas.session import RepairSessionContext
from app.voice.interfaces import VoiceInput
from app.voice.sync_adapters import SyncSTTAdapter, SyncTTSAdapter
from app.voice.speech_to_text import DeterministicSTT, WhisperSTT
from app.voice.text_to_speech import DeterministicTTS, LocalTTS


@pytest.mark.asyncio
async def test_whisper_italian(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": " ciao mondo "}
    mock_whisper = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    monkeypatch.setitem(__import__("sys").modules, "whisper", mock_whisper)

    audio = tmp_path / "test_audio_it.wav"
    audio.write_bytes(b"RIFFfake")

    stt = WhisperSTT(model_name="base")
    result = await stt.transcribe(audio, language="it")

    assert isinstance(result, str)
    assert len(result) > 0
    assert "ciao" in result.lower()
    mock_model.transcribe.assert_called_once()


@pytest.mark.asyncio
async def test_whisper_transcribe_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "display rotto"}
    mock_whisper = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    monkeypatch.setitem(__import__("sys").modules, "whisper", mock_whisper)

    stt = WhisperSTT(model_name="base")
    result = await stt.transcribe_stream(b"RIFF-stream")

    assert "display" in result.lower()


@pytest.mark.asyncio
async def test_tts_speaks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_audio = b"RIFF....wav-data"

    mock_engine = MagicMock()

    def _save_to_file(text: str, path: str) -> None:
        Path(path).write_bytes(fake_audio)

    mock_engine.save_to_file.side_effect = _save_to_file
    mock_engine.runAndWait.return_value = None

    mock_pyttsx3 = MagicMock()
    mock_pyttsx3.init.return_value = mock_engine
    monkeypatch.setitem(__import__("sys").modules, "pyttsx3", mock_pyttsx3)

    tts = LocalTTS()
    audio = await tts.speak("Ciao, come stai?")

    assert isinstance(audio, bytes)
    assert len(audio) > 0
    assert audio == fake_audio


@pytest.mark.asyncio
async def test_tts_speak_stream() -> None:
    tts = DeterministicTTS(payload=b"abc1234567890")
    chunks = [chunk async for chunk in tts.speak_stream("Ciao")]
    assert len(chunks) == 1
    assert chunks[0] == b"abc1234567890"


@pytest.mark.asyncio
async def test_deterministic_stt_italian() -> None:
    stt = DeterministicSTT(default_text="problema display iphone")
    result = await stt.transcribe_stream(b"audio-bytes")
    assert "display" in result.lower()


def test_sync_stt_adapter() -> None:
    adapter = SyncSTTAdapter(DeterministicSTT(default_text="problema ricarica"))
    result = adapter.transcribe(VoiceInput(audio_reference="audio-1"))
    assert "ricarica" in result.text.lower()


def test_sync_tts_adapter() -> None:
    adapter = SyncTTSAdapter(DeterministicTTS(payload=b"wav-bytes"))
    output = adapter.synthesize("Ciao laboratorio")
    assert output.audio_reference.startswith("tts:")


@pytest.mark.asyncio
async def test_process_voice_input() -> None:
    engine = ConversationCommandEngine(
        stt=DeterministicSTT(default_text="ciao"),
        tts=DeterministicTTS(payload=b"audio-response"),
    )
    session = RepairSessionContext(repair_session_id="repair-voice-1")

    result = await engine.process_voice_input(
        b"fake-audio",
        session,
        session_id="repair-voice-1",
        device_id="pc-1",
    )

    assert result["transcript"] == "ciao"
    assert result["listening"]["message"] == "Ascoltando..."
    assert isinstance(result.get("audio"), bytes)
    assert result["text"]

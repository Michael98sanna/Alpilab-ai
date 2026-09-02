"""Tests for deterministic .env loading and provider key validation."""

from __future__ import annotations

import json
import sys
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.learning_engine import LearningEngine
from app.ai.providers.diagnostics import probe_ollama
from app.ai.providers.key_validation import assert_no_secrets_in_text, key_present, key_shape_valid
from app.ai.providers.ollama import LOCAL_MODEL_MAX_CONFIDENCE, OllamaProvider
from app.ai.providers.registry import load_providers
from app.ai.router import BrainRouter
from app.ai.schemas import TaskType
from app.config import env_loader
from app.config.env_loader import get_env_load_state, load_environment
from app.main import app
from app.models.database import Base
from app.models.orm_models import DiagnosticCard


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def card(db_session):
    card_id = str(uuid.uuid4())
    db_session.add(
        DiagnosticCard(
            id=card_id,
            session_id="repair-test",
            device_id="iphone-13",
            device_name="iPhone 13",
        )
    )
    db_session.commit()
    return card_id


def test_env_file_from_alpilab_env_file(tmp_path, monkeypatch):
    custom = tmp_path / "custom.env"
    custom.write_text(
        "OPENAI_API_KEY=sk-test12345678901234567890123456789012\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ALPILAB_ENV_FILE", str(custom))
    load_environment(force=True)
    assert key_present("OPENAI_API_KEY")


def test_non_frozen_searches_build_release_not_python_executable_dir(tmp_path, monkeypatch):
    root = tmp_path / "project"
    release = root / "build" / "release"
    release.mkdir(parents=True)
    (release / ".env").write_text("ALPILAB_TEST_VALUE=release\n", encoding="utf-8")
    monkeypatch.chdir(root)
    monkeypatch.delenv("ALPILAB_ENV_FILE", raising=False)
    monkeypatch.setattr(env_loader, "is_frozen", lambda: False)
    monkeypatch.setattr(env_loader, "install_dir", lambda: root)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python-install" / "python.exe"))

    loaded = load_environment(force=True)
    searched = get_env_load_state()["env_file_searched"]

    assert loaded == (release / ".env").resolve()
    assert any(
        entry["origin"] == "build_release" and entry["path"] == str(release / ".env")
        for entry in searched
    )
    assert any(
        entry["origin"] == "executable_dir" and entry["outcome"] == "skipped_not_frozen"
        for entry in searched
    )
    assert all("python-install" not in str(entry["path"]) for entry in searched)


def test_frozen_search_uses_executable_directory_and_skips_build_release(tmp_path, monkeypatch):
    executable_dir = tmp_path / "release"
    executable_dir.mkdir()
    exe_env = executable_dir / ".env"
    exe_env.write_text("ALPILAB_TEST_VALUE=frozen\n", encoding="utf-8")
    monkeypatch.delenv("ALPILAB_ENV_FILE", raising=False)
    monkeypatch.setattr(env_loader, "is_frozen", lambda: True)
    monkeypatch.setattr(env_loader, "install_dir", lambda: executable_dir)

    loaded = load_environment(force=True)
    searched = get_env_load_state()["env_file_searched"]

    assert loaded == exe_env.resolve()
    assert any(
        entry["origin"] == "executable_dir" and entry["path"] == str(exe_env) and entry["outcome"] == "found"
        for entry in searched
    )
    assert any(
        entry["origin"] == "build_release" and entry["outcome"] == "skipped_not_frozen"
        for entry in searched
    )


def test_env_search_trace_contains_origins_and_outcomes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ALPILAB_ENV_FILE", raising=False)
    monkeypatch.setattr(env_loader, "is_frozen", lambda: False)
    monkeypatch.setattr(env_loader, "install_dir", lambda: tmp_path / "project")

    load_environment(force=True)
    searched = get_env_load_state()["env_file_searched"]

    assert {"executable_dir", "build_release", "cwd", "project_root"} <= {
        entry["origin"] for entry in searched
    }
    assert all({"path", "origin", "outcome"} <= entry.keys() for entry in searched)
    assert any(entry["outcome"] == "skipped_not_frozen" for entry in searched)


def test_explicit_env_file_precedes_environment_variable(tmp_path, monkeypatch):
    from_env = tmp_path / "from-env.env"
    explicit = tmp_path / "explicit.env"
    from_env.write_text("ALPILAB_TEST_VALUE=environment\n", encoding="utf-8")
    explicit.write_text("ALPILAB_TEST_VALUE=explicit\n", encoding="utf-8")
    monkeypatch.setenv("ALPILAB_ENV_FILE", str(from_env))
    monkeypatch.setattr(env_loader, "is_frozen", lambda: False)
    monkeypatch.setattr(env_loader, "install_dir", lambda: tmp_path / "project")

    loaded = load_environment(force=True, env_file=explicit)

    assert loaded == explicit.resolve()
    assert get_env_load_state()["env_file_loaded_from"] == "explicit_argument"


def test_explicit_missing_env_file_errors_without_automatic_fallback(tmp_path, monkeypatch, capsys):
    fallback = tmp_path / "fallback.env"
    fallback.write_text("ALPILAB_TEST_VALUE=fallback\n", encoding="utf-8")
    missing = tmp_path / "missing.env"
    monkeypatch.setenv("ALPILAB_ENV_FILE", str(fallback))

    with pytest.raises(FileNotFoundError, match="file .env indicato non esiste"):
        load_environment(force=True, env_file=missing)

    from scripts import check_api_keys

    monkeypatch.setattr(sys, "argv", ["check_api_keys.py", "--offline", "--env-file", str(missing)])
    assert check_api_keys.main() == 2
    output = capsys.readouterr().err
    assert "Errore:" in output
    assert str(fallback) not in output


def test_env_search_state_never_contains_secret_values(tmp_path, monkeypatch):
    secret = "sk-this-must-never-appear"
    env_file = tmp_path / "safe.env"
    env_file.write_text(f"OPENAI_API_KEY={secret}\n", encoding="utf-8")
    load_environment(force=True, env_file=env_file)

    payload = json.dumps(get_env_load_state())
    assert secret not in payload


def test_empty_key_is_treated_as_missing(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "   ")
    assert not key_present("OPENAI_API_KEY")
    providers = load_providers()
    assert all(provider.name != "gpt4" for provider in providers)


def test_malformed_prefix_still_loads_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "bad-key-value")
    assert key_present("OPENAI_API_KEY")
    assert not key_shape_valid("OPENAI_API_KEY")
    providers = load_providers()
    assert any(provider.name == "gpt4" for provider in providers)


def test_ollama_health_reports_model_missing(monkeypatch):
    provider = OllamaProvider(enabled=True)
    monkeypatch.setattr(
        "app.ai.providers.diagnostics.ollama_model_installed",
        lambda base_url, model: False,
    )
    row = probe_ollama(provider, live=True)
    assert row["error_kind"] == "model_missing"
    assert row["available"] is False


def test_ollama_response_confidence_is_capped(monkeypatch):
    provider = OllamaProvider(enabled=True)

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "Risposta locale"}

    monkeypatch.setattr(
        "httpx.Client.post",
        lambda self, *args, **kwargs: FakeResponse(),
    )
    result = provider.complete("test")
    assert result.confidence <= LOCAL_MODEL_MAX_CONFIDENCE


def test_ollama_outcome_does_not_index_kb(db_session, card):
    engine = LearningEngine(db_session)
    confirmation = engine.record_feedback(
        card_id=card,
        feedback="confirmed",
        provider="ollama",
        pre_confidence=0.4,
    )
    with patch.object(engine.kb, "index_case") as index_mock, patch.object(
        engine.kb, "boost_confidence"
    ) as boost_mock:
        engine.record_outcome(
            confirmation.id,
            outcome="success",
            symptom_text="display nero",
            ai_diagnosis="test",
            ai_solution="fix",
        )
        index_mock.assert_not_called()
        boost_mock.assert_not_called()


def test_providers_status_never_leaks_secrets(client, monkeypatch):
    class EmptyKnowledgeBase:
        embedder_kind = "disabled"
        model_name = "disabled"

        def __init__(self, _db):
            pass

        def indexed_case_count(self):
            return 0

    monkeypatch.setattr("app.api.routes.ai_brain.SmartKnowledgeBase", EmptyKnowledgeBase)
    monkeypatch.setattr(
        "app.api.routes.ai_brain._provider_status_cache",
        {"ts": 0.0, "payload": {}},
    )
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test12345678901234567890123456789012")
    response = client.get("/api/v1/ai/providers/status")
    assert response.status_code == 200
    payload = json.dumps(response.json())
    assert "sk-test12345678901234567890123456789012" not in payload
    assert_no_secrets_in_text(payload)


def test_router_online_route_caps_ollama_confidence(db_session):
    class FakeOllama:
        name = "ollama"
        model = "llama3.2"
        priority = 99
        is_configured = True

        def complete(self, prompt, *, system_prompt=None, temperature=0.3, max_tokens=1024):
            from app.ai.schemas import LLMResponse

            return LLMResponse(
                provider="ollama",
                model="llama3.2",
                content="ok",
                confidence=0.9,
            )

    router = BrainRouter(db_session, providers=[FakeOllama()])
    result = router._online_route("test", TaskType.QUICK_ANSWER, 0.0, "disabled")
    assert result.confidence <= 0.45

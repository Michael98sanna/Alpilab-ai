"""Tests for Gemini key validation and provider error classification."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import httpx
import pytest

from app.ai.providers.diagnostics import probe_cloud_provider
from app.ai.providers.errors import ACTIONS_IT, classify_error_text, classify_exception
from app.ai.providers.gemini import GEMINI_API_BASE, GeminiAPIError, GeminiProvider
from app.ai.providers.key_validation import google_key_shape_valid, key_shape_valid


def test_google_aq_key_shape_valid(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AQ.AbC123xyz789012345678901234567890")
    assert key_shape_valid("GOOGLE_API_KEY") is True
    assert google_key_shape_valid("AQ.AbC123xyz789012345678901234567890") is True


def test_google_aiza_key_shape_valid(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSyAbC123xyz789012345678901234567")
    assert key_shape_valid("GOOGLE_API_KEY") is True
    assert google_key_shape_valid("AIzaSyAbC123xyz789012345678901234567") is True


def test_google_bad_prefix_shape_invalid(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "XX-not-a-google-key")
    assert key_shape_valid("GOOGLE_API_KEY") is False
    assert google_key_shape_valid("XX-not-a-google-key") is False


def test_access_token_type_unsupported_maps_to_dedicated_error_kind():
    message = (
        '{"error":{"code":401,"message":"Request had invalid authentication credentials.",'
        '"status":"UNAUTHENTICATED","details":[{"reason":"ACCESS_TOKEN_TYPE_UNSUPPORTED"}]}}'
    )
    kind = classify_error_text(message, status_code=401)
    assert kind == "auth_key_format_unsupported"
    assert kind != "unreachable"
    assert kind != "auth_failed"
    assert "generativelanguage.googleapis.com" in ACTIONS_IT[kind]


def test_fake_openai_key_classified_as_auth_failed_not_unreachable():
    class AuthenticationError(Exception):
        status_code = 401

    exc = AuthenticationError("Error code: 401 - Incorrect API key provided: sk-fake")
    assert classify_exception(exc) == "auth_failed"


def test_gemini_fake_key_probe_reports_auth_failed(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSyFakeKeyForTestingOnly1234567890")

    provider = GeminiProvider(enabled=True)

    def fake_post(*args, **kwargs):
        response = MagicMock()
        response.status_code = 400
        response.text = json.dumps(
            {
                "error": {
                    "code": 400,
                    "message": "API key not valid. Please pass a valid API key.",
                    "status": "INVALID_ARGUMENT",
                }
            }
        )
        response.reason_phrase = "Bad Request"
        return response

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    row = probe_cloud_provider(provider, live=True)
    assert row["error_kind"] == "auth_failed"
    assert row["error_kind"] != "unreachable"


def test_gemini_access_token_type_unsupported_from_http(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AQ.AbFakeKeyForTestingOnly1234567890")
    provider = GeminiProvider(enabled=True)

    def fake_post(*args, **kwargs):
        response = MagicMock()
        response.status_code = 401
        response.text = json.dumps(
            {
                "error": {
                    "code": 401,
                    "message": "Request had invalid authentication credentials.",
                    "status": "UNAUTHENTICATED",
                    "details": [{"reason": "ACCESS_TOKEN_TYPE_UNSUPPORTED"}],
                }
            }
        )
        response.reason_phrase = "Unauthorized"
        return response

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    with pytest.raises(GeminiAPIError) as exc_info:
        provider.complete("ping")

    row = probe_cloud_provider(provider, live=True)
    assert row["error_kind"] == "auth_key_format_unsupported"
    assert exc_info.value.status_code == 401


def test_gemini_uses_native_generative_language_endpoint():
    assert GEMINI_API_BASE == "https://generativelanguage.googleapis.com/v1beta"

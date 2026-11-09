"""Unit tests for the Ollama client and response cleaning (no network)."""

import pytest
import requests
from fastapi import HTTPException

import main


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_call_ollama_sends_model_and_prompt(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured.update(url=url, body=json, timeout=timeout)
        return _FakeResponse({"response": "  Answer text  "})

    monkeypatch.setattr(main.requests, "post", fake_post)

    assert main.call_ollama("Explain limits") == "Answer text"
    assert captured["url"] == main.OLLAMA_URL
    assert captured["body"]["model"] == main.OLLAMA_MODEL
    assert captured["body"]["prompt"] == "Explain limits"
    assert captured["body"]["stream"] is False


def test_call_ollama_turns_connection_errors_into_http_500(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(main.requests, "post", fake_post)

    with pytest.raises(HTTPException) as error:
        main.call_ollama("anything")
    assert error.value.status_code == 500
    assert "Ollama request failed" in error.value.detail


def test_clean_ai_response_removes_non_latin_text_and_extra_blank_lines():
    raw = "Line one 你好\n\n\n\nLine two Привет  "
    assert main.clean_ai_response(raw) == "Line one \n\nLine two"


def test_clean_ai_response_keeps_turkish_characters():
    assert main.clean_ai_response("Türev ve integral: ğüşıöç") == "Türev ve integral: ğüşıöç"

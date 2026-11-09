import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Always point the app at a throwaway in-memory database before main.py is
# imported (main.py creates its tables at import time), even if DATABASE_URL
# is set in the shell, so tests can never touch a real database.
os.environ["DATABASE_URL"] = "sqlite://"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main  # noqa: E402
from models import Base  # noqa: E402


@pytest.fixture
def db_session_factory():
    """A fresh in-memory SQLite database for every test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def fake_llm(monkeypatch):
    """Replace the Ollama call so tests never need a running model.

    Records every prompt it receives so tests can check what was sent.
    """
    prompts = []

    def _fake_call_ollama(prompt: str):
        prompts.append(prompt)
        return "FAKE AI ANSWER"

    monkeypatch.setattr(main, "call_ollama", _fake_call_ollama)
    return prompts


@pytest.fixture
def client(db_session_factory, fake_llm):
    def _override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[main.get_db] = _override_get_db
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


def make_pdf(text: str | None) -> bytes:
    """Build a minimal one-page PDF. With text=None the page has no text."""
    if text is None:
        stream = b""
    else:
        safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET".encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_start = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode()
    out += f"startxref\n{xref_start}\n%%EOF\n".encode()
    return bytes(out)


@pytest.fixture
def pdf_bytes():
    return make_pdf

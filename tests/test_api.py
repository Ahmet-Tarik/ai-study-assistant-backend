"""API tests for folders, notes, documents and the AI endpoints.

The database is an in-memory SQLite per test and the Ollama call is
replaced by a fake (see conftest.py), so the suite runs offline.
"""


# --- health -----------------------------------------------------------------

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "project": "AI Study Assistant"}


# --- folders ----------------------------------------------------------------

def test_folder_crud(client):
    created = client.post("/folders", json={"name": "Calculus"})
    assert created.status_code == 200
    folder = created.json()
    assert folder["name"] == "Calculus"

    listed = client.get("/folders").json()
    assert [f["name"] for f in listed] == ["Calculus"]

    renamed = client.put(f"/folders/{folder['id']}", json={"name": "Calculus II"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Calculus II"

    deleted = client.delete(f"/folders/{folder['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted_folder_id"] == folder["id"]
    assert client.get("/folders").json() == []


def test_folder_not_found(client):
    assert client.put("/folders/999", json={"name": "x"}).status_code == 404
    assert client.delete("/folders/999").status_code == 404


def test_deleting_folder_unassigns_its_notes_and_documents(client, pdf_bytes):
    folder_id = client.post("/folders", json={"name": "Physics"}).json()["id"]
    note_id = client.post(
        "/notes", json={"title": "Waves", "content": "Wave basics", "folder_id": folder_id}
    ).json()["id"]
    document_id = client.post(
        "/documents/upload-pdf",
        files={"file": ("waves.pdf", pdf_bytes("Wave equation"), "application/pdf")},
        data={"folder_id": str(folder_id)},
    ).json()["id"]

    assert client.delete(f"/folders/{folder_id}").status_code == 200

    assert client.get(f"/notes/{note_id}").json()["folder_id"] is None
    assert client.get(f"/documents/{document_id}").json()["folder_id"] is None


def test_create_folder_requires_name(client):
    assert client.post("/folders", json={}).status_code == 422


# --- notes ------------------------------------------------------------------

def test_note_crud(client):
    created = client.post("/notes", json={"title": "Limits", "content": "A limit is..."})
    assert created.status_code == 200
    note = created.json()
    assert note["title"] == "Limits"
    assert note["folder_id"] is None

    assert client.get(f"/notes/{note['id']}").json()["content"] == "A limit is..."
    assert len(client.get("/notes").json()) == 1

    updated = client.put(
        f"/notes/{note['id']}", json={"title": "Limits v2", "content": "Updated"}
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Limits v2"

    deleted = client.delete(f"/notes/{note['id']}")
    assert deleted.status_code == 200
    assert client.get(f"/notes/{note['id']}").status_code == 404


def test_note_with_unknown_folder_is_rejected(client):
    response = client.post(
        "/notes", json={"title": "t", "content": "c", "folder_id": 42}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Folder not found"


def test_note_not_found(client):
    assert client.get("/notes/999").status_code == 404
    assert client.put("/notes/999", json={"title": "t", "content": "c"}).status_code == 404
    assert client.delete("/notes/999").status_code == 404


def test_note_validation_error(client):
    assert client.post("/notes", json={"title": "missing content"}).status_code == 422


# --- AI endpoints (LLM faked) -----------------------------------------------

def test_summarize_text_sends_text_to_llm(client, fake_llm):
    response = client.post("/ai/summarize", json={"text": "Photosynthesis converts light."})
    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == "FAKE AI ANSWER"
    assert body["original_text_length"] == len("Photosynthesis converts light.")
    assert "Photosynthesis converts light." in fake_llm[0]


def test_generate_quiz_uses_question_count(client, fake_llm):
    response = client.post("/ai/generate-quiz", json={"text": "Cells", "question_count": 3})
    assert response.status_code == 200
    assert response.json()["question_count"] == 3
    assert "Create 3 quiz questions" in fake_llm[0]


def test_chat_requires_context(client, fake_llm):
    response = client.post("/ai/chat", json={"message": "What is a cell?", "context": "   "})
    assert response.status_code == 400
    assert fake_llm == []


def test_chat_with_note_uses_note_as_context(client, fake_llm):
    note_id = client.post(
        "/notes", json={"title": "Bio", "content": "Mitochondria make ATP."}
    ).json()["id"]

    response = client.post(f"/notes/{note_id}/chat", json={"message": "What makes ATP?"})
    assert response.status_code == 200
    assert response.json()["answer"] == "FAKE AI ANSWER"
    assert "Mitochondria make ATP." in fake_llm[0]
    assert "What makes ATP?" in fake_llm[0]


def test_note_summary_and_quiz(client, fake_llm):
    note_id = client.post("/notes", json={"title": "T", "content": "Content"}).json()["id"]
    assert client.post(f"/notes/{note_id}/summarize").json()["summary"] == "FAKE AI ANSWER"
    quiz = client.post(f"/notes/{note_id}/generate-quiz?question_count=2")
    assert quiz.status_code == 200
    assert quiz.json()["question_count"] == 2


def test_ai_on_missing_note_returns_404(client, fake_llm):
    assert client.post("/notes/999/summarize").status_code == 404
    assert client.post("/notes/999/chat", json={"message": "hi"}).status_code == 404
    assert fake_llm == []


# --- PDF files and documents ------------------------------------------------

def test_extract_pdf_text(client, pdf_bytes):
    response = client.post(
        "/files/extract-pdf-text",
        files={"file": ("lecture.pdf", pdf_bytes("Hello PDF"), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "lecture.pdf"
    assert body["page_count"] == 1
    assert "Hello PDF" in body["text"]


def test_non_pdf_upload_is_rejected(client):
    response = client.post(
        "/files/extract-pdf-text",
        files={"file": ("notes.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are allowed"


def test_corrupt_pdf_is_rejected(client):
    response = client.post(
        "/files/extract-pdf-text",
        files={"file": ("broken.pdf", b"not really a pdf", "application/pdf")},
    )
    assert response.status_code == 400


def test_pdf_without_text_cannot_be_summarized(client, pdf_bytes, fake_llm):
    response = client.post(
        "/files/summarize-pdf",
        files={"file": ("blank.pdf", pdf_bytes(None), "application/pdf")},
    )
    assert response.status_code == 400
    assert fake_llm == []


def test_document_lifecycle(client, pdf_bytes, fake_llm):
    uploaded = client.post(
        "/documents/upload-pdf",
        files={"file": ("ch1.pdf", pdf_bytes("Chapter one text"), "application/pdf")},
    )
    assert uploaded.status_code == 200
    document_id = uploaded.json()["id"]

    assert len(client.get("/documents").json()) == 1
    assert "Chapter one text" in client.get(f"/documents/{document_id}").json()["content"]

    folder_id = client.post("/folders", json={"name": "Course"}).json()["id"]
    moved = client.put(f"/documents/{document_id}/folder", json={"folder_id": folder_id})
    assert moved.json()["folder_id"] == folder_id

    chat = client.post(f"/documents/{document_id}/chat", json={"message": "Summarize"})
    assert chat.status_code == 200
    assert "Chapter one text" in fake_llm[-1]

    assert client.post(f"/documents/{document_id}/summarize").status_code == 200

    assert client.delete(f"/documents/{document_id}").status_code == 200
    assert client.get(f"/documents/{document_id}").status_code == 404


def test_upload_into_unknown_folder_is_rejected(client, pdf_bytes):
    response = client.post(
        "/documents/upload-pdf",
        files={"file": ("a.pdf", pdf_bytes("text"), "application/pdf")},
        data={"folder_id": "77"},
    )
    assert response.status_code == 404
    assert client.get("/documents").json() == []

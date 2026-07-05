from io import BytesIO
import re

import requests
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, Document, Folder, Note

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"

app = FastAPI(title="AI Study Assistant Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


class FolderCreate(BaseModel):
    name: str



class FolderUpdate(BaseModel):
    name: str


class DocumentFolderUpdate(BaseModel):
    folder_id: int | None = None


class NoteCreate(BaseModel):
    title: str
    content: str
    folder_id: int | None = None


class NoteUpdate(BaseModel):
    title: str
    content: str
    folder_id: int | None = None


class TextSummarizeRequest(BaseModel):
    text: str


class TextQuizRequest(BaseModel):
    text: str
    question_count: int = 5


class TextChatRequest(BaseModel):
    message: str
    context: str = ""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def clean_ai_response(text: str):
    blocked_unicode_pattern = r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\u0600-\u06ff\u0400-\u04ff]+"
    cleaned_text = re.sub(blocked_unicode_pattern, "", text)
    cleaned_text = cleaned_text.replace("回收中", "")
    cleaned_text = cleaned_text.replace("请稍候", "")
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    return cleaned_text.strip()


def validate_folder(folder_id: int | None, db: Session):
    if folder_id is None:
        return

    folder = db.query(Folder).filter(Folder.id == folder_id).first()

    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")


def call_ollama(prompt: str):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                },
            },
            timeout=120,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise HTTPException(
            status_code=500,
            detail=f"Ollama request failed: {str(error)}",
        )

    data = response.json()
    raw_response = data.get("response", "")
    return clean_ai_response(raw_response)


def generate_summary(text: str):
    prompt = f"""
You are an AI study assistant.

Summarize the following study material in clear, simple English.

Rules:
- Always answer in English.
- Write a real summary, not a long rewritten version of the material.
- Use maximum 5 bullet points.
- Each bullet point must be 1 short sentence.
- Keep technical terms in correct academic English.
- Do not use LaTeX notation; write formulas in plain text.
- Do not use Chinese, Japanese, Korean, Arabic, Cyrillic, or any non-Latin characters.
- Do not output random symbols or broken characters.

Text:
{text}
"""
    return call_ollama(prompt)


def generate_quiz(text: str, question_count: int):
    prompt = f"""
You are an AI study assistant.

Create {question_count} quiz questions from the following study material.

Rules:
- Always answer in English.
- Do not write an introduction.
- Number the questions.
- After each question, write the correct answer.
- Keep the questions clear and short.
- Use correct academic English.
- Do not use LaTeX notation; write formulas in plain text like c_n * (x - a)^n.
- Use this exact format:

Question 1:
Answer:

Question 2:
Answer:

Text:
{text}
"""
    return call_ollama(prompt)


def generate_chat_answer(message: str, context: str):
    prompt = f"""
You are an AI study assistant.

CRITICAL OUTPUT RULES:
- Always answer in English unless the user explicitly asks for another language.
- Use clear, natural, study-friendly English.
- Keep the answer short, focused, and easy to understand.
- Use correct academic terminology.
- Do not use LaTeX notation; write formulas in plain text like c_n * (x - a)^n.
- Do not translate technical terms awkwardly.
- Do not use Chinese, Japanese, Korean, Arabic, Cyrillic, or any non-Latin characters.
- Do not output random symbols or broken characters.
- If the user asks for a summary, write a real summary, not a long rewritten version of the whole material.
- For summaries, use maximum 5 bullet points.
- Each bullet point must be 1 short sentence.

CONTENT RULES:
- Use only the provided study material as context.
- Do not add information that is not supported by the study material.
- If the study material does not include enough information, say that clearly.
- Answer the user's exact question.
- Prefer clean bullet points when they make the answer easier to study.

Study material:
{context}

User question:
{message}

Final answer:
"""
    return call_ollama(prompt)


def extract_text_from_pdf_content(file_content: bytes):
    try:
        pdf_reader = PdfReader(BytesIO(file_content))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read PDF file")

    extracted_text = ""

    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_text += page_text + "\n"

    return pdf_reader, extracted_text


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "project": "AI Study Assistant",
    }


@app.post("/ai/summarize")
def summarize_text(request: TextSummarizeRequest):
    summary = generate_summary(request.text)

    return {
        "summary": summary,
        "original_text_length": len(request.text),
    }


@app.post("/ai/generate-quiz")
def generate_quiz_from_text(request: TextQuizRequest):
    quiz = generate_quiz(request.text, request.question_count)

    return {
        "quiz": quiz,
        "question_count": request.question_count,
        "original_text_length": len(request.text),
    }


@app.post("/ai/chat")
def chat_with_context(request: TextChatRequest):
    if not request.context.strip():
        raise HTTPException(status_code=400, detail="Context is required for this endpoint")

    answer = generate_chat_answer(request.message, request.context)

    return {
        "answer": answer,
        "message_length": len(request.message),
        "context_length": len(request.context),
    }


# Folder endpoints
@app.get("/folders")
def get_folders(db: Session = Depends(get_db)):
    folders = db.query(Folder).all()
    return folders


@app.post("/folders")
def create_folder(folder: FolderCreate, db: Session = Depends(get_db)):
    new_folder = Folder(name=folder.name)

    db.add(new_folder)
    db.commit()
    db.refresh(new_folder)

    return new_folder


@app.put("/folders/{folder_id}")
def update_folder(folder_id: int, updated_folder: FolderUpdate, db: Session = Depends(get_db)):
    folder = db.query(Folder).filter(Folder.id == folder_id).first()

    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder.name = updated_folder.name

    db.commit()
    db.refresh(folder)

    return folder


@app.delete("/folders/{folder_id}")
def delete_folder(folder_id: int, db: Session = Depends(get_db)):
    folder = db.query(Folder).filter(Folder.id == folder_id).first()

    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")

    notes = db.query(Note).filter(Note.folder_id == folder_id).all()
    documents = db.query(Document).filter(Document.folder_id == folder_id).all()

    for note in notes:
        note.folder_id = None

    for document in documents:
        document.folder_id = None

    db.delete(folder)
    db.commit()

    return {
        "message": "Folder deleted successfully",
        "deleted_folder_id": folder_id,
    }


@app.post("/files/extract-pdf-text")
async def extract_pdf_text(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_content = await file.read()
    pdf_reader, extracted_text = extract_text_from_pdf_content(file_content)

    return {
        "filename": file.filename,
        "page_count": len(pdf_reader.pages),
        "text_length": len(extracted_text),
        "text": extracted_text,
    }


@app.post("/files/summarize-pdf")
async def summarize_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_content = await file.read()
    pdf_reader, extracted_text = extract_text_from_pdf_content(file_content)

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from this PDF")

    summary = generate_summary(extracted_text)

    return {
        "filename": file.filename,
        "page_count": len(pdf_reader.pages),
        "text_length": len(extracted_text),
        "summary": summary,
    }


# Document endpoints
@app.post("/documents/upload-pdf")
async def upload_pdf_as_document(
    file: UploadFile = File(...),
    folder_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    validate_folder(folder_id, db)

    file_content = await file.read()
    pdf_reader, extracted_text = extract_text_from_pdf_content(file_content)

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from this PDF")

    new_document = Document(
        filename=file.filename,
        content=extracted_text,
        folder_id=folder_id,
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return {
        "id": new_document.id,
        "filename": new_document.filename,
        "folder_id": new_document.folder_id,
        "page_count": len(pdf_reader.pages),
        "text_length": len(new_document.content),
    }


@app.get("/documents")
def get_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).all()
    return documents



@app.get("/documents/{document_id}")
def get_document_by_id(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@app.put("/documents/{document_id}/folder")
def update_document_folder(
    document_id: int,
    updated_document: DocumentFolderUpdate,
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    validate_folder(updated_document.folder_id, db)

    document.folder_id = updated_document.folder_id

    db.commit()
    db.refresh(document)

    return document


@app.post("/documents/{document_id}/summarize")
def summarize_document_by_id(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    summary = generate_summary(document.content)

    return {
        "document_id": document.id,
        "filename": document.filename,
        "summary": summary,
        "original_text_length": len(document.content),
    }


@app.post("/documents/{document_id}/chat")
def chat_with_document(document_id: int, request: TextChatRequest, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    answer = generate_chat_answer(request.message, document.content)

    return {
        "document_id": document.id,
        "filename": document.filename,
        "answer": answer,
        "message_length": len(request.message),
        "context_length": len(document.content),
    }


@app.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(document)
    db.commit()

    return {
        "message": "Document deleted successfully",
        "deleted_document_id": document_id,
    }


@app.get("/notes")
def get_notes(db: Session = Depends(get_db)):
    notes = db.query(Note).all()
    return notes


@app.post("/notes")
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    validate_folder(note.folder_id, db)
    new_note = Note(
        title=note.title,
        content=note.content,
        folder_id=note.folder_id,
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return new_note


@app.get("/notes/{note_id}")
def get_note_by_id(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()

    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


@app.post("/notes/{note_id}/summarize")
def summarize_note_by_id(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()

    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    summary = generate_summary(note.content)

    return {
        "note_id": note.id,
        "title": note.title,
        "summary": summary,
        "original_text_length": len(note.content),
    }


@app.post("/notes/{note_id}/generate-quiz")
def generate_quiz_from_note(note_id: int, question_count: int = 5, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()

    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    quiz = generate_quiz(note.content, question_count)

    return {
        "note_id": note.id,
        "title": note.title,
        "quiz": quiz,
        "question_count": question_count,
        "original_text_length": len(note.content),
    }


@app.post("/notes/{note_id}/chat")
def chat_with_note(note_id: int, request: TextChatRequest, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()

    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    answer = generate_chat_answer(request.message, note.content)

    return {
        "note_id": note.id,
        "title": note.title,
        "answer": answer,
        "message_length": len(request.message),
        "context_length": len(note.content),
    }


@app.put("/notes/{note_id}")
def update_note(note_id: int, updated_note: NoteUpdate, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()

    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    validate_folder(updated_note.folder_id, db)

    note.title = updated_note.title
    note.content = updated_note.content
    note.folder_id = updated_note.folder_id

    db.commit()
    db.refresh(note)

    return note


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()

    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()

    return {
        "message": "Note deleted successfully",
        "deleted_note": note,
    }
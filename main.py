from io import BytesIO
import re

import requests
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, Document, Note

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


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteUpdate(BaseModel):
    title: str
    content: str


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

Summarize the following study material in a clear and short way.
Use simple language.

Rules:
- Write a real summary, not a long rewritten version of the material.
- Use maximum 5 bullet points.
- Each bullet point must be 1 short sentence.
- If the material is Turkish, answer in Turkish.
- If the material is English, answer in English.
- Do not use Chinese, Japanese, Korean, Arabic, Cyrillic, or any non-Latin characters.
- Avoid awkward literal translations.

Text:
{text}
"""
    return call_ollama(prompt)


def generate_quiz(text: str, question_count: int):
    prompt = f"""
Create {question_count} quiz questions from the following study note.

Rules:
- Do not write an introduction.
- Number the questions.
- After each question, write the correct answer.
- Keep the questions clear and short.
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
    turkish_characters = "çğıöşüÇĞİÖŞÜ"
    turkish_keywords = ["basit", "türkçe", "anlat", "açıkla", "sadece", "kısmı", "özet", "özetle"]

    message_lower = message.lower()
    should_answer_turkish = any(character in message for character in turkish_characters) or any(
        keyword in message_lower for keyword in turkish_keywords
    )

    answer_language = "Turkish" if should_answer_turkish else "English"

    prompt = f"""
You are an AI study assistant.

CRITICAL OUTPUT RULES:
- Answer language: {answer_language}.
- If answer language is Turkish, write natural, clear, everyday Turkish.
- Do NOT translate word-by-word from English to Turkish.
- If a technical English word sounds more natural than a Turkish translation, keep the English word.
- Do NOT use strange or literal translations.
- Do NOT use Chinese, Japanese, Korean, Arabic, Cyrillic, or any non-Latin characters.
- Do NOT translate any sentence into Chinese, Japanese, Korean, Arabic, or Cyrillic.
- Do NOT output random symbols or broken characters.
- Keep the answer very short, focused, and easy to understand.
- If the user asks for a summary, write a real summary, not a long rewritten version of the whole material.
- For summaries, use maximum 5 bullet points.
- Each bullet point must be 1 short sentence.

CONTENT RULES:
- Use only the provided study material as context.
- Do not add information that is not supported by the study material.
- If the study material does not include enough information, say that clearly.
- Answer the user's exact question.
- Prefer clean bullet points.
- Avoid awkward, literal, or unnatural Turkish translations.
- In Turkish, use simple and general wording that fits the user's question instead of forcing specific terms from one topic.

Study material:
{context}

User question:
{message}

Final answer in {answer_language}:
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
async def upload_pdf_as_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_content = await file.read()
    pdf_reader, extracted_text = extract_text_from_pdf_content(file_content)

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from this PDF")

    new_document = Document(
        filename=file.filename,
        content=extracted_text,
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return {
        "id": new_document.id,
        "filename": new_document.filename,
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


@app.get("/notes")
def get_notes(db: Session = Depends(get_db)):
    notes = db.query(Note).all()
    return notes


@app.post("/notes")
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    new_note = Note(
        title=note.title,
        content=note.content,
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

    note.title = updated_note.title
    note.content = updated_note.content

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
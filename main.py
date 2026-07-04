from io import BytesIO

import requests
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from pypdf import PdfReader
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, Note

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"

app = FastAPI(title="AI Study Assistant Backend")

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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def call_ollama(prompt: str):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
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
    return data.get("response", "")


def generate_summary(text: str):
    prompt = f"""
Summarize the following study note in a clear and short way.
Use simple language.

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
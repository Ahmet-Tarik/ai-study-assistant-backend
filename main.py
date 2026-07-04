from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import requests

from database import SessionLocal, engine
from models import Base, Note

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


def generate_summary(text: str):
    prompt = f"""
Summarize the following study note in a clear and short way.
Use simple language.

Text:
{text}
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise HTTPException(
            status_code=500,
            detail=f"Ollama request failed: {str(error)}"
        )

    data = response.json()
    return data.get("response", "")


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

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise HTTPException(
            status_code=500,
            detail=f"Ollama request failed: {str(error)}"
        )

    data = response.json()
    return data.get("response", "")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "project": "AI Study Assistant"
    }


@app.post("/ai/summarize")
def summarize_text(request: TextSummarizeRequest):
    summary = generate_summary(request.text)

    return {
        "summary": summary,
        "original_text_length": len(request.text)
    }


@app.post("/ai/generate-quiz")
def generate_quiz_from_text(request: TextQuizRequest):
    quiz = generate_quiz(request.text, request.question_count)

    return {
        "quiz": quiz,
        "question_count": request.question_count,
        "original_text_length": len(request.text)
    }


@app.get("/notes")
def get_notes(db: Session = Depends(get_db)):
    notes = db.query(Note).all()
    return notes


@app.post("/notes")
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    new_note = Note(
        title=note.title,
        content=note.content
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
        "original_text_length": len(note.content)
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
        "original_text_length": len(note.content)
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
        "deleted_note": note
    }
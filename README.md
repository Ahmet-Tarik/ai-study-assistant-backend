# AI Study Assistant Backend

AI Study Assistant Backend is a FastAPI-based backend project for managing study notes, generating AI-powered summaries and quizzes, and extracting/summarizing PDF content using a local LLM through Ollama.

This project is built as a practical backend and AI integration project to improve my software engineering skills.

## Features

- Create, read, update, and delete study notes
- Store notes in a local SQLite database
- Generate AI-powered summaries from plain text
- Generate AI-powered summaries from saved notes
- Generate AI-powered quizzes from plain text
- Generate AI-powered quizzes from saved notes
- Extract text from uploaded PDF files
- Summarize uploaded PDF files
- Use a local LLM through Ollama
- Interactive API documentation with Swagger UI

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Ollama
- Qwen2.5:7b
- pypdf
- python-multipart

## API Endpoints

```text
GET    /health
POST   /ai/summarize
POST   /ai/generate-quiz
GET    /notes
POST   /notes
GET    /notes/{note_id}
PUT    /notes/{note_id}
DELETE /notes/{note_id}
POST   /notes/{note_id}/summarize
POST   /notes/{note_id}/generate-quiz
POST   /files/extract-pdf-text
POST   /files/summarize-pdf
```

## How to Run

Clone the repository:

```bash
git clone https://github.com/Ahmet-Tarik/ai-study-assistant-backend.git
cd ai-study-assistant-backend
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Open Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

## Ollama Setup

Install Ollama and pull the model:

```bash
ollama pull qwen2.5:7b
```

The AI endpoints use this local model through Ollama.

## Example AI Summarization Request

Endpoint:

```text
POST /ai/summarize
```

Request body:

```json
{
  "text": "DFA is a deterministic finite automaton. It has states, transitions, an alphabet, a start state, and accept states."
}
```

Example response:

```json
{
  "summary": "A DFA consists of states, transitions, an input alphabet, a starting state, and accept states.",
  "original_text_length": 115
}
```

## Example Saved Note Summarization Request

Endpoint:

```text
POST /notes/{note_id}/summarize
```

Example response:

```json
{
  "note_id": 1,
  "title": "DFA Notes",
  "summary": "A DFA is a finite-state machine used to recognize regular languages.",
  "original_text_length": 429
}
```

## Example AI Quiz Generation Request

Endpoint:

```text
POST /ai/generate-quiz
```

Request body:

```json
{
  "text": "A DFA is a deterministic finite automaton used to recognize regular languages.",
  "question_count": 3
}
```

Example response:

```json
{
  "quiz": "Question 1:\nWhat does a DFA recognize?\nAnswer: Regular languages.",
  "question_count": 3,
  "original_text_length": 78
}
```

## Example PDF Text Extraction

Endpoint:

```text
POST /files/extract-pdf-text
```

This endpoint accepts a PDF file upload and returns extracted text from the PDF.

Example response:

```json
{
  "filename": "example.pdf",
  "page_count": 6,
  "text_length": 8353,
  "text": "Extracted PDF text..."
}
```

## Example PDF Summarization

Endpoint:

```text
POST /files/summarize-pdf
```

This endpoint accepts a PDF file upload, extracts text from it, and summarizes the extracted text using the local Ollama model.

Example response:

```json
{
  "filename": "example.pdf",
  "page_count": 6,
  "text_length": 8353,
  "summary": "The PDF explains prompt requirements, grading expectations, and final checklist rules."
}
```

## Project Status

Current version includes:

- Notes CRUD API
- SQLite database persistence
- Local AI text summarization with Ollama and Qwen2.5
- Saved note summarization by note ID
- AI quiz generation from text and saved notes
- PDF text extraction
- PDF summarization
- Swagger documentation

Planned next steps:

- Save generated summaries to the database
- Save generated quizzes to the database
- Add authentication
- Add Docker support
- Improve response formatting for quiz outputs
- Add frontend UI

## Author

Ahmet Tarık Sevinç
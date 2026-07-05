# AI Study Assistant Backend

AI Study Assistant Backend is a FastAPI-based backend project for managing study notes, uploading PDF study materials, and chatting with those materials using a local LLM through Ollama.

The backend supports notes, PDF documents, AI summarization, quiz generation, and contextual AI chat. It is built as a practical backend and AI integration project to improve software engineering skills.

## Features

- Create, read, update, and delete study notes
- Store notes in a local SQLite database
- Generate AI-powered summaries from plain text
- Generate AI-powered quizzes from plain text
- Summarize saved notes by note ID
- Generate quizzes from saved notes by note ID
- Chat with saved notes using their content as context
- Extract text from uploaded PDF files
- Summarize uploaded PDF files
- Save uploaded PDFs as documents in the database
- List saved PDF documents
- Chat with saved PDF documents using extracted PDF text as context
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
POST   /ai/chat

POST   /files/extract-pdf-text
POST   /files/summarize-pdf

GET    /notes
POST   /notes
GET    /notes/{note_id}
PUT    /notes/{note_id}
DELETE /notes/{note_id}
POST   /notes/{note_id}/summarize
POST   /notes/{note_id}/generate-quiz
POST   /notes/{note_id}/chat

POST   /documents/upload-pdf
GET    /documents
GET    /documents/{document_id}
POST   /documents/{document_id}/summarize
POST   /documents/{document_id}/chat
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

## Example Saved Note Chat Request

Endpoint:

```text
POST /notes/{note_id}/chat
```

Request body:

```json
{
  "message": "Sadece NFA kısmını basit Türkçe anlat."
}
```

Example response:

```json
{
  "note_id": 2,
  "title": "Long DFA and NFA Study Notes",
  "answer": "NFA, bir giriş sembolü için birden fazla olası geçişe sahip olabilir...",
  "message_length": 38,
  "context_length": 1850
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

## Example PDF Document Upload

Endpoint:

```text
POST /documents/upload-pdf
```

This endpoint accepts a PDF file upload, extracts its text, and saves it as a document in the SQLite database.

Example response:

```json
{
  "id": 1,
  "filename": "MultiFacts Quick-Check Guidelines.pdf",
  "page_count": 6,
  "text_length": 8353
}
```

## Example PDF Document Chat Request

Endpoint:

```text
POST /documents/{document_id}/chat
```

Request body:

```json
{
  "message": "Bu PDF'deki final checklist kısmını basitçe anlat."
}
```

Example response:

```json
{
  "document_id": 1,
  "filename": "MultiFacts Quick-Check Guidelines.pdf",
  "answer": "Final kontrol listesi, promptun yeterli sayıda gerçek içerdiğini, net olduğunu ve beklentilerin doğru yazıldığını kontrol etmeyi ister.",
  "message_length": 58,
  "context_length": 8353
}
```

## Project Status

Current version includes:

- Notes CRUD API
- SQLite database persistence
- Local AI summarization with Ollama and Qwen2.5
- AI quiz generation from text and saved notes
- Contextual chat with saved notes
- PDF text extraction
- PDF summarization
- PDF document storage
- Contextual chat with saved PDF documents
- Swagger documentation
- CORS support for the local frontend

Planned next steps:

- Save generated summaries and quizzes to the database
- Add delete/update endpoints for saved documents
- Add authentication
- Add Docker support
- Improve response formatting for quiz outputs
- Improve frontend README and deployment instructions

## Related Repository

Frontend repository:

```text
https://github.com/Ahmet-Tarik/ai-study-assistant-frontend
```

## Author

Ahmet Tarık Sevinç

# AI Study Assistant Backend

AI Study Assistant Backend is a FastAPI-based backend for managing study notes, uploading PDF study materials, organizing sources into folders, and chatting with those materials using a local LLM through Ollama.

The project is built as a practical backend and AI integration project. It includes CRUD operations, PDF text extraction, contextual AI chat, AI summaries, quiz generation, and folder-based organization for notes and PDF documents.

## Features

- Create, read, update, and delete study notes
- Create and delete folders for organizing study sources
- Assign notes and PDF documents to folders
- Move saved PDF documents between folders
- Store notes, folders, and PDF documents in a local SQLite database
- Generate AI-powered summaries from plain text
- Generate AI-powered quizzes from plain text
- Summarize saved notes by note ID
- Generate quizzes from saved notes by note ID
- Chat with saved notes using their content as context
- Extract text from uploaded PDF files
- Summarize uploaded PDF files
- Save uploaded PDFs as documents in the database
- List saved PDF documents
- Delete saved PDF documents
- Chat with saved PDF documents using extracted PDF text as context
- Use a local LLM through Ollama
- English-first AI responses for cleaner academic output
- Interactive API documentation with Swagger UI
- CORS support for the local React frontend

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

GET    /folders
POST   /folders
PUT    /folders/{folder_id}
DELETE /folders/{folder_id}

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
PUT    /documents/{document_id}/folder
POST   /documents/{document_id}/summarize
POST   /documents/{document_id}/chat
DELETE /documents/{document_id}
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

Make sure Ollama is running before using AI endpoints:

```bash
ollama serve
```

Default Ollama endpoint used by the backend:

```text
http://localhost:11434/api/generate
```

## Database

The backend uses SQLite for local persistence.

Stored data includes:

- Folders
- Study notes
- Uploaded PDF documents
- Extracted PDF text

If the database schema changes during development, the local SQLite database file can be deleted and recreated automatically when the server restarts.

## Example Folder Creation

Endpoint:

```text
POST /folders
```

Request body:

```json
{
  "name": "Mathematics"
}
```

Example response:

```json
{
  "id": 1,
  "name": "Mathematics"
}
```

## Example Note Creation With Folder

Endpoint:

```text
POST /notes
```

Request body:

```json
{
  "title": "Calculus - Power Series",
  "content": "A power series is an infinite series written using powers of (x - a).",
  "folder_id": 1
}
```

Example response:

```json
{
  "id": 1,
  "title": "Calculus - Power Series",
  "content": "A power series is an infinite series written using powers of (x - a).",
  "folder_id": 1
}
```

## Example AI Summarization Request

Endpoint:

```text
POST /ai/summarize
```

Request body:

```json
{
  "text": "A DFA is a deterministic finite automaton. It has states, transitions, an alphabet, a start state, and accept states."
}
```

Example response:

```json
{
  "summary": "- A DFA is a deterministic finite automaton.\n- It has states, transitions, an alphabet, a start state, and accept states.",
  "original_text_length": 123
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
  "quiz": "Question 1:\nWhat is a DFA used to recognize?\nAnswer: Regular languages.",
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
  "message": "Summarize this note in simple English."
}
```

Example response:

```json
{
  "note_id": 1,
  "title": "Calculus - Power Series",
  "answer": "- A power series is an infinite series using powers of (x - a).\n- The center of the series is a.\n- The ratio test can help find the radius of convergence.",
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
  "summary": "- The PDF explains prompt requirements.\n- It includes grading expectations and checklist rules."
}
```

## Example PDF Document Upload With Folder

Endpoint:

```text
POST /documents/upload-pdf
```

This endpoint accepts a PDF file upload, extracts its text, and saves it as a document in the SQLite database.

It also supports an optional `folder_id` form field.

Example response:

```json
{
  "id": 1,
  "filename": "MultiFacts Quick-Check Guidelines.pdf",
  "folder_id": 1,
  "page_count": 6,
  "text_length": 8353
}
```

## Example Move PDF Document To Folder

Endpoint:

```text
PUT /documents/{document_id}/folder
```

Request body:

```json
{
  "folder_id": 1
}
```

To move a PDF document back to Uncategorized, send:

```json
{
  "folder_id": null
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
  "message": "Summarize the final checklist section in simple English."
}
```

Example response:

```json
{
  "document_id": 1,
  "filename": "MultiFacts Quick-Check Guidelines.pdf",
  "answer": "- The checklist helps verify that the prompt is clear.\n- It checks whether the expected answer is specific and complete.",
  "message_length": 58,
  "context_length": 8353
}
```

## Project Status

Current version includes:

- Notes CRUD API
- Folder CRUD API
- Folder assignment for notes and documents
- PDF document folder update endpoint
- SQLite database persistence
- Local AI summarization with Ollama and Qwen2.5
- AI quiz generation from text and saved notes
- Contextual chat with saved notes
- PDF text extraction
- PDF summarization
- PDF document storage
- PDF document deletion
- Contextual chat with saved PDF documents
- English-first AI response formatting
- Plain-text formula output instead of LaTeX-style formatting
- Swagger documentation
- CORS support for the local frontend

Planned next steps:

- Save generated summaries and quizzes to the database
- Save chat history to the backend
- Add authentication
- Add user accounts
- Add Docker support
- Add deployment configuration

## Related Repository

Frontend repository:

```text
https://github.com/Ahmet-Tarik/ai-study-assistant-frontend
```

## Author

Ahmet Tarık Sevinç
# AI Study Assistant Backend

AI Study Assistant Backend is a FastAPI-based backend project for managing study notes and generating AI-powered summaries using a local LLM through Ollama.

This project is built as a practical backend and AI integration project to improve my software engineering skills.

## Features

- Create, read, update, and delete study notes
- Store notes in a local SQLite database
- Generate AI-powered summaries from text
- Use a local LLM through Ollama
- Interactive API documentation with Swagger UI

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Ollama
- Qwen2.5:7b

## API Endpoints

```text
GET    /health
POST   /ai/summarize
GET    /notes
POST   /notes
GET    /notes/{note_id}
PUT    /notes/{note_id}
DELETE /notes/{note_id}
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

The AI summarization endpoint uses this local model through Ollama.

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

## Project Status

Current version includes:

- Notes CRUD API
- SQLite database persistence
- Local AI text summarization with Ollama and Qwen2.5
- Swagger documentation

Planned next steps:

- Summarize saved notes by note ID
- Add PDF upload
- Extract text from PDF files
- Generate quizzes from study notes
- Add authentication
- Add Docker support

## Author

Ahmet Tarık Sevinç
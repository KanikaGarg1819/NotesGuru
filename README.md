# NotesGuru 📚

A Syllabus-Driven AI Study Portal that turns handwritten notes into structured, exam-ready study guides.

---

## What it does

1. Student uploads a photo of handwritten notes
2. App cleans the image and extracts text via OCR
3. Notes are matched to syllabus chapters using vector similarity
4. Gaps in coverage are detected automatically
5. Gemini AI generates a clean, exam-ready study guide

---

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14, Tailwind CSS, Shadcn/ui |
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL 15 |
| Cache / Queue | Redis + Celery |
| OCR | Google Cloud Vision API + Tesseract |
| Image Processing | OpenCV, Pillow |
| AI Matching | sentence-transformers, FAISS |
| AI Generation | Google Gemini 1.5 Pro |
| Storage | AWS S3 |
| Containerisation | Docker + Docker Compose |

---

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/NotesGuru.git
cd NotesGuru
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `GEMINI_API_KEY` — from [Google AI Studio](https://aistudio.google.com)
- `GOOGLE_APPLICATION_CREDENTIALS` — path to your GCloud Vision key JSON
- `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` — from AWS IAM
- `SECRET_KEY` — generate with `openssl rand -hex 32`

### 3. Run with Docker

```bash
docker compose up --build
```

This starts:
- FastAPI backend → http://localhost:8000
- Next.js frontend → http://localhost:3000
- PostgreSQL → port 5432
- Redis → port 6379
- Celery worker (background tasks)

### 4. API docs

Once running, open:
- Swagger UI → http://localhost:8000/docs
- ReDoc → http://localhost:8000/redoc

---

## Project structure

```
NotesGuru/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # FastAPI route handlers
│   │   ├── core/              # Config, settings
│   │   ├── db/                # Database session
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── tasks/             # Celery background tasks
│   │   └── main.py            # App entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                   # Next.js App Router pages
│   ├── components/            # React components
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Build phases

- [x] Phase 1 — Project structure + Docker + FastAPI skeleton
- [ ] Phase 2 — PostgreSQL models (User, Syllabus, Note, Guide)
- [ ] Phase 3 — Image preprocessing (OpenCV)
- [ ] Phase 4 — OCR integration (Google Vision)
- [ ] Phase 5 — Syllabus matching (sentence-transformers + FAISS)
- [ ] Phase 6 — Gap detection
- [ ] Phase 7 — Gemini content generation
- [ ] Phase 8 — Celery background tasks
- [ ] Phase 9 — Frontend UI
- [ ] Phase 10 — Auth + full integration

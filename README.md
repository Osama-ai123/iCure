# iCure — AI-Powered Medical Chatbot

> A full-stack RAG-based medical chatbot built end-to-end with Python, Flask, FAISS, and Gemini AI — with a lightweight bilingual web interface.

---

## Overview

iCure answers medical questions in Arabic and English using **Retrieval-Augmented Generation (RAG)**. Instead of relying solely on a language model's general knowledge, iCure retrieves relevant medical information from a curated dataset before generating an answer — making responses more accurate and grounded in real medical data.

The system supports multi-turn conversations through session-based memory, handles informal Arabic medical terminology, ships with a bilingual web interface, and is fully containerized with Docker and automated through CI/CD.

---

## Architecture

```
Web Interface (HTML / CSS / JavaScript)
        │  fetch → JSON
        ▼
┌─────────────────────────┐
│   Flask REST API        │  ← session management, request validation
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│   Query Normalization   │  ← Gemini resolves ambiguous follow-ups
│   (Gemini API)          │    and transliterates informal terms
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│   Sentence Embedding    │  ← paraphrase-multilingual-MiniLM-L12-v2
│   (sentence-transformers)│   converts question to a 384-dim vector
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│   Semantic Search       │  ← FAISS IndexFlatL2 searches 250K vectors
│   (FAISS)               │   returns top-5 most relevant Q&A pairs
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│   Answer Generation     │  ← Gemini 2.5 Flash generates a response
│   (Gemini API)          │   grounded strictly in retrieved context
└─────────────────────────┘
        │
        ▼
     JSON Response → rendered in the browser
```

---

## Key Features

- **Semantic Search** — finds relevant medical information by meaning, not keyword matching
- **Multilingual Support** — handles Arabic and English questions in the same system
- **Bilingual Web Interface** — RTL-first UI that detects the language of each message and sets its text direction automatically
- **Query Normalization** — resolves follow-up questions ("How do I treat it?") and transliterates informal Arabic medical terms (e.g. "انيميا" → anemia)
- **Session Memory** — maintains conversation context across multiple exchanges per session
- **Out-of-scope Detection** — declines non-medical questions gracefully
- **Fault Tolerance** — automatic retry logic for API failures, with graceful error states surfaced in the UI
- **Containerized** — fully Dockerized for consistent deployment anywhere
- **CI/CD** — automated Docker image build and push via GitHub Actions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, vanilla JavaScript (Fetch API) |
| Backend Framework | Python + Flask, Flask-CORS |
| Embedding Model | `paraphrase-multilingual-MiniLM-L12-v2` |
| Vector Database | FAISS (IndexFlatL2, 250K vectors, 384 dimensions) |
| Language Model | Gemini 2.5 Flash (via `google-genai`) |
| Data Processing | Pandas, NumPy |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Version Control | Git / GitHub |

---

## Dataset

- **Source:** English medical Q&A dataset (Question, Answer, Category)
- **Original size:** 808,472 rows across 91 categories
- **After cleaning:** ~570,000 rows across 45 categories
- **Embeddings generated on:** 250,000 sampled rows (GPU-accelerated, NVIDIA RTX 4050)

**Cleaning steps applied:**
- Removed null and duplicate rows
- Merged semantically overlapping categories (e.g. Dental Diseases + Oral Diseases + Teeth Health → Dental)
- Removed non-medical categories (Medical News, Ecology, Organic Chemistry)
- Dropped categories with fewer than 150 samples
- Filtered out rows with very short questions (< 5 words) or answers (< 10 words)

---

## Web Interface

A single-page interface (`frontend/index.html`) that talks to the API directly — no build step, no framework, no dependencies.

**What it does:**
- Sends questions to `POST /ask` and renders answers as chat bubbles
- Generates a `session_id` on page load so the server can track conversation history
- Detects whether each message is Arabic or English and sets its direction accordingly — the model replies in the language of the question, so an English answer inside an RTL page needs its own direction
- Shows a typing indicator and disables the send button while a request is in flight, preventing duplicate submissions
- Distinguishes network failures (`catch`) from server-side error responses (`!response.ok`) and surfaces each with an appropriate message
- Clears both the visible chat and the server-side session via `POST /clear`

**Running it:**

```bash
# 1. Start the API
python app.py

# 2. Open the interface
frontend/index.html
```

Open the file directly in a browser. The API must be running on `http://localhost:5000` — CORS is enabled server-side to allow the request.

---

## API Endpoints

### `GET /`
Health check — confirms the API is running.

**Response:**
```json
{
  "status": "iCure API is running",
  "version": "1.0"
}
```

---

### `POST /ask`
Submit a medical question and receive an AI-generated answer.

**Request Body:**
```json
{
  "question": "ما هي أعراض فقر الدم؟",
  "session_id": "user-123"
}
```

**Response:**
```json
{
  "question": "ما هي أعراض فقر الدم؟",
  "answer": "تشمل أعراض فقر الدم: التعب والإرهاق، شحوب الوجه، الدوخة، ضيق التنفس...",
  "session_id": "user-123",
  "status": "success"
}
```

**Notes:**
- `session_id` is optional. If omitted, defaults to `"default"`
- The API maintains the last 6 messages (3 exchanges) per session
- Responds in the same language as the question

---

### `POST /clear`
Clear the conversation history for a session.

**Request Body:**
```json
{
  "session_id": "user-123"
}
```

**Response:**
```json
{
  "status": "session cleared",
  "session_id": "user-123"
}
```

---

## How Session Memory Works

Each request includes a `session_id`. The server maintains a conversation history per session and automatically injects it into the prompt — the client only needs to send the current question.

```
Request 1:  {"question": "What are symptoms of diabetes?",  "session_id": "abc"}
Response 1: "Symptoms include frequent urination, thirst..."

Request 2:  {"question": "What is the treatment?",  "session_id": "abc"}
            ↑ Server resolves "the treatment" → "treatment for diabetes"
Response 2: "Treatment includes diet management, medication..."
```

---

## Project Structure

```
iCure/
├── app.py                  # Flask API — endpoints and session management
├── rag_pipeline.py         # Core RAG logic — search, normalize, generate
├── Clean.py                # Data cleaning and preprocessing script
├── faiss_builder.py        # FAISS index construction
├── train.py                # Embedding generation (GPU)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build instructions
├── .dockerignore           # Excludes large files from Docker image
├── .gitignore              # Excludes data files and secrets from Git
├── frontend/
│   └── index.html          # Bilingual web interface (HTML + CSS + JS)
└── .github/
    └── workflows/
        └── docker-build.yml  # CI/CD pipeline
```

---

## Running with Docker

**1. Build the image:**
```bash
docker build -t icure .
```

**2. Run the container with data volumes:**
```bash
docker run -p 5000:5000 \
  --env-file .env \
  -v "/path/to/data:/app" \
  icure
```

**3. Test the API:**
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are symptoms of diabetes?", "session_id": "test"}'
```

---

## Environment Variables

Create a `.env` file with the following:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## CI/CD Pipeline

Every push to `main` automatically:
1. Checks out the latest code
2. Authenticates with Docker Hub
3. Builds the Docker image
4. Pushes the updated image to Docker Hub

Pipeline defined in: `.github/workflows/docker-build.yml`

---

## Design Decisions

**Why RAG instead of fine-tuning?**
Fine-tuning requires significant compute and retraining when data changes. RAG allows updating the knowledge base simply by rebuilding the FAISS index — no retraining needed.

**Why FAISS over a traditional database?**
Medical questions require semantic understanding, not keyword matching. FAISS finds conceptually similar content even when exact words differ.

**Why multilingual embeddings?**
The dataset is in English while users ask in Arabic. A multilingual model maps both languages into the same vector space, enabling cross-lingual search without translation overhead.

**Why query normalization before search?**
Follow-up questions like "How do I treat it?" contain no medical content for FAISS to match. Normalization rewrites them as standalone questions before retrieval.

**Why session memory is server-side?**
Putting history management on the server keeps the client API simple — users only send their current question and a session ID.

**Why vanilla JavaScript for the frontend?**
The interface is a single page with minimal state. React would have added a build step and a dependency tree without solving a problem the project actually has.

**Why per-message direction detection?**
The page is RTL, but the model answers in the language of the question. An English answer rendered inside an RTL container places its punctuation incorrectly, so each message is checked for Arabic characters and given its own direction.

---

## Sample Interactions

**Arabic question:**
```
Q: ما هي أعراض فقر الدم؟
A: تشمل أعراض فقر الدم: التعب والإرهاق العام، شحوب الوجه والجفون،
   الدوخة، ضيق التنفس، تسارع ضربات القلب...
```

**English question:**
```
Q: What causes high blood pressure?
A: High blood pressure can be caused by genetic factors, high-sodium diet,
   obesity, stress, smoking, and certain medical conditions...
```

**Follow-up question (session memory):**
```
Q: ما هي أعراض فقر الدم؟  → [detailed answer]
Q: كيف أعالجها؟           → [treatment for anemia — context resolved automatically]
```

**Out-of-scope question:**
```
Q: What is the best restaurant in Amman?
A: I don't have enough information about this topic.
   Always consult a doctor for medical decisions.
```

---

## Known Limitations & Roadmap

Current constraints, and what's planned next:

- **Session storage is in-process** — conversation history lives in a Python dictionary, so it is lost on restart and will not work across multiple instances. Redis is the planned replacement.
- **CORS is open to all origins** — appropriate for local development, but should be restricted to a specific domain before any public deployment.
- **No automated tests yet** — the CI pipeline builds the image but does not verify behaviour. Adding pytest coverage to the workflow is the next step.
- **Not yet deployed** — the application runs locally and in Docker. Deployment to AWS EC2, with data artifacts served from S3, is planned.

---

## Author

**Osama Jehad AL-Karasneh**
Computer Engineering Graduate — Yarmouk University
[LinkedIn](https://linkedin.com/in/osama-al-karasneh) • [GitHub](https://github.com/Osama-ai123)

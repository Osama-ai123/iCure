# iCure — AI-Powered Medical Chatbot API

> A production-ready RAG-based medical chatbot API built end-to-end with Python, Flask, FAISS, and Gemini AI.

---

## Overview

iCure is a backend API that answers medical questions in Arabic and English using **Retrieval-Augmented Generation (RAG)**. Instead of relying solely on a language model's general knowledge, iCure retrieves relevant medical information from a curated dataset before generating an answer — making responses more accurate and grounded in real medical data.

The system supports multi-turn conversations through session-based memory, handles informal Arabic medical terminology, and is fully containerized with Docker and automated through CI/CD.

---

## Architecture

```
User Question (Arabic or English)
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
     JSON Response
```

---

## Key Features

- **Semantic Search** — finds relevant medical information by meaning, not keyword matching
- **Multilingual Support** — handles Arabic and English questions in the same system
- **Query Normalization** — resolves follow-up questions ("How do I treat it?") and transliterates informal Arabic medical terms (e.g. "انيميا" → anemia)
- **Session Memory** — maintains conversation context across multiple exchanges per session
- **Out-of-scope Detection** — declines non-medical questions gracefully
- **Fault Tolerance** — automatic retry logic for API failures
- **Containerized** — fully Dockerized for consistent deployment anywhere
- **CI/CD** — automated Docker image build and push via GitHub Actions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Python + Flask |
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

## Author

**Osama Jehad AL-Karasneh**
Computer Engineering Graduate — Yarmouk University
[LinkedIn](https://linkedin.com/in/osama-al-karasneh) • [GitHub](https://github.com/Osama-ai123)

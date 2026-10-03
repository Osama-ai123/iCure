# iCure — AI-Powered Medical Chatbot

> A full-stack RAG-based medical chatbot built end-to-end with Python, Flask, FAISS, PostgreSQL, and Gemini AI — with JWT authentication, persistent conversations, a Docker Compose stack (Nginx, Gunicorn, PostgreSQL), and a CI pipeline on GitHub Actions.

---

## Overview

iCure answers medical questions in Arabic and English using **Retrieval-Augmented Generation (RAG)**. Instead of relying solely on a language model's general knowledge, iCure retrieves relevant medical information from a curated dataset before generating an answer — making responses grounded in real medical data.

Users create an account, sign in, and chat. Every conversation is stored in PostgreSQL, survives server restarts, and appears in a sidebar where it can be reopened or deleted. Each user can only ever see their own conversations.

The whole system — web interface, API, and database — starts with a single `docker compose up`, and database migrations run automatically on startup.

---

## Architecture

```
                Browser (HTML / CSS / vanilla JS)
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│  Nginx  (web)                                            │
│  • serves the static frontend                            │
│  • proxies /api/*  →  app:5000                           │
└──────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│  Flask API on Gunicorn  (app)                            │
│  • JWT auth: register / login / refresh / logout         │
│  • conversations & messages (SQLAlchemy ORM)             │
│  • RAG pipeline:                                         │
│      Gemini rewrites the question (follow-ups, terms)    │
│        → multilingual embedding (384-dim)                │
│        → FAISS search over 250K vectors (top-5)          │
│        → Gemini answers from the retrieved context only  │
└──────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│  PostgreSQL 16  (db)                                     │
│  users · conversations · messages · refresh_tokens       │
│  schema managed by Alembic migrations                    │
└──────────────────────────────────────────────────────────┘
```

---

## Key Features

- **Semantic Search** — finds relevant medical information by meaning, not keyword matching
- **Multilingual** — Arabic and English questions in the same system, answered in the language asked
- **Query Normalization** — resolves follow-ups ("How do I treat it?") and transliterated Arabic medical terms (e.g. "انيميا" → anemia) before retrieval
- **User Accounts** — registration and login with bcrypt-hashed passwords
- **JWT Authentication** — short-lived access tokens with refresh tokens, refreshed automatically by the frontend
- **Persistent Conversations** — history stored in PostgreSQL; context survives restarts and works across server instances
- **Per-user Isolation** — every query is scoped to the authenticated user (IDOR-tested)
- **Conversation Sidebar** — list, reopen, and delete past conversations
- **Database Migrations** — schema versioned with Alembic and applied automatically on container start
- **One-command Stack** — Docker Compose runs Nginx, the API on Gunicorn, and PostgreSQL together
- **CI** — every push to `main` builds the Docker image and pushes it to Docker Hub

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, vanilla JavaScript (Fetch API) |
| Web server / reverse proxy | Nginx |
| Backend | Python 3.12, Flask, Gunicorn |
| Authentication | bcrypt, PyJWT (HS256) |
| Database | PostgreSQL 16, SQLAlchemy 2.0 (ORM), Alembic |
| Embedding model | `paraphrase-multilingual-MiniLM-L12-v2` (CPU) |
| Vector search | FAISS (IndexFlatL2, 250K vectors, 384 dimensions) |
| Language model | Gemini 2.5 Flash (`google-genai`) |
| Data processing | Pandas, NumPy |
| Containers | Docker, Docker Compose |
| CI | GitHub Actions → Docker Hub |
| Cloud | AWS EC2 (Ubuntu), S3, IAM |

---

## Quick Start (Docker Compose)

**Prerequisites:** Docker Desktop, a Gemini API key, and the two data files (`faiss_index.bin`, `ample_data_250K.csv`).

**1. Configure the environment**

```bash
cp .env.example .env
# then fill in GEMINI_API_KEY, JWT_SECRET and POSTGRES_PASSWORD
```

Generate a strong `JWT_SECRET` with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**2. Provide the data files**

Place them in `data/` — or leave the folder empty and provide AWS credentials, and the app will download them from S3 on first start.

```
data/
├── faiss_index.bin
└── ample_data_250K.csv
```

**3. Start the stack**

```bash
docker compose up --build -d
```

On first start the embedding model is downloaded into a cached volume; later starts are fast. Open **http://localhost**, create an account, and start asking.

**Useful commands**

```bash
docker compose ps                # service status
docker compose logs -f app       # API logs
docker compose down              # stop (data is kept)
docker compose down -v           # stop AND delete the database volume
```

### Local development without Compose

For fast iteration, run only PostgreSQL in Docker and the API directly:

```bash
docker run -d --name icure-db -e POSTGRES_PASSWORD=devpassword -e POSTGRES_DB=icure -p 5432:5432 postgres:16
alembic upgrade head
python app.py
```

Then open `frontend/index.html` directly in the browser. The page detects that it was opened from disk and calls `http://localhost:5000`; when served by Nginx it calls `/api` instead.

---

## Authentication Design

| | Access token | Refresh token |
|---|---|---|
| Format | JWT (HS256) | Random 256-bit string (`secrets.token_urlsafe`) |
| Lifetime | 15 minutes | 7 days |
| Stored server-side | No — verified by signature alone | Yes — only its SHA-256 hash |
| Sent with | Every protected request (`Authorization: Bearer …`) | Only `/refresh` and `/logout` |
| Revocable | No (expires quickly instead) | Yes — deleted on logout |

**Why two tokens?** A long-lived token is convenient but dangerous if stolen; a short-lived one is safe but forces frequent logins. The access token is sent constantly but dies in 15 minutes; the refresh token is sent rarely and can be revoked. When a request returns `401 Token expired`, the frontend calls `/refresh` and retries the original request transparently.

**Why bcrypt for passwords but SHA-256 for refresh tokens?** Passwords are chosen by humans and are guessable, so they need a deliberately slow, salted hash. Refresh tokens are 256 bits of randomness that cannot be guessed, so a fast hash is enough — and it allows a direct indexed lookup.

**Other decisions**

- Login returns the same `401 Invalid email or password` whether the email or the password is wrong, so it does not reveal which accounts exist.
- Emails are normalized (`strip().lower()`) on both register and login.
- Password length is checked in **bytes** (bcrypt's 72-byte limit), since an Arabic character takes two bytes in UTF-8.
- Duplicate registrations are caught twice: a lookup for the common case, and the database `UNIQUE` constraint (`IntegrityError` → `409`) for the race where two requests arrive at the same moment.
- `JWT_SECRET` and `DATABASE_URL` are read from the environment, and the app refuses to start if they are missing (fail fast).

---

## Data Model

```
users                       conversations                  messages
─────                       ─────────────                  ────────
id (PK)              ┌───<  id (PK)                ┌───<   id (PK)
email (UNIQUE)       │      user_id (FK, indexed) ─┘       conversation_id (FK, indexed)
pass_hash            │      title                          content (TEXT)
created_at           │      created_at                     role  ENUM(question, response)
                     │                                     sent_time
                     │      refresh_tokens
                     │      ──────────────
                     └───<  user_id (FK, indexed)
                            token_hash (UNIQUE)
                            expires_at (timestamptz)
                            created_at
```

All foreign keys use `ON DELETE CASCADE`: deleting a user removes their conversations, messages, and tokens. The conversation title is taken from the first question.

---

## API Endpoints

All protected endpoints require `Authorization: Bearer <access_token>`.

### Auth

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| `POST` | `/register` | `{email, password}` | `201 {id, email}` | `400` invalid input · `409` email exists |
| `POST` | `/login` | `{email, password}` | `200 {access_token, refresh_token, token_type, expires_in}` | `400` missing fields · `401` invalid credentials |
| `POST` | `/refresh` | `{refresh_token}` | `200 {access_token, token_type, expires_in}` | `401` invalid or expired |
| `POST` | `/logout` | `{refresh_token}` | `204` | `400` missing token |

### Chat (protected)

| Method | Path | Description |
|---|---|---|
| `POST` | `/ask` | Ask a question. Omit `conversation_id` to start a new conversation. |
| `GET` | `/conversations` | The current user's conversations, newest first. |
| `GET` | `/conversations/<id>/messages` | Messages of one conversation, in order. |
| `DELETE` | `/conversations/<id>` | Delete a conversation and its messages (`204`). |

Requesting or deleting another user's conversation returns `404`, the same as a conversation that does not exist.

**`POST /ask` example**

```json
// request
{ "question": "ما هي أعراض فقر الدم؟", "conversation_id": null }

// response
{
  "question": "ما هي أعراض فقر الدم؟",
  "answer": "تشمل أعراض فقر الدم: التعب والإرهاق، شحوب الوجه، الدوخة...",
  "conversation_id": 12,
  "status": "success"
}
```

Send the returned `conversation_id` with the next question to continue the same conversation. The last 6 messages are used as context. If the language model is unavailable, the API returns `503`, and a conversation that was just created is removed so no empty conversations are left behind.

### Health

`GET /` — confirms the API is running.

---

## Project Structure

```
main project/
├── app.py                 # Flask routes: auth, ask, conversations
├── auth.py                # bcrypt, JWT, refresh tokens, @require_auth
├── rag_pipeline.py        # normalization, embedding, FAISS search, generation
├── db/
│   ├── database.py        # engine, SessionLocal, Base (reads DATABASE_URL)
│   └── models.py          # User, Conversation, Message, RefreshToken
├── alembic/               # migrations (env.py + versions/)
├── alembic.ini
├── frontend/
│   ├── index.html         # login/register, chat, sidebar
│   ├── logo.jpg
│   └── logo-wordmark.png
├── data/                  # FAISS index + dataset (not in Git, not in the image)
├── Dockerfile             # Python 3.12-slim, CPU-only PyTorch, Gunicorn
├── docker-compose.yml     # db (Postgres) · app (API) · web (Nginx)
├── nginx.conf             # static files + /api reverse proxy
├── requirements.txt       # pinned dependencies
├── .env.example           # required environment variables (no secrets)
└── .dockerignore
```

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Gemini API key |
| `JWT_SECRET` | Secret used to sign access tokens |
| `POSTGRES_PASSWORD` | Password for the Compose PostgreSQL service |
| `DATABASE_URL` | Used when running without Compose, e.g. `postgresql+psycopg2://postgres:devpassword@localhost:5432/icure` (Compose sets it automatically) |
| `S3_BUCKET` | Bucket holding the data files (optional if they are already in `data/`) |
| `SQL_ECHO` | `1` to log every SQL statement (debugging) |
| `WEB_PORT` | Host port for Nginx (default `80`) |

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

## Containers and Deployment

**Image design**

- `python:3.12-slim` base, matching the development environment.
- PyTorch is installed from the **CPU-only** index before the other requirements. The default Linux wheel pulls several GB of CUDA libraries that are useless without a GPU — on the first attempt it exhausted the build disk and crashed Docker.
- All dependencies are pinned. An unpinned SQLAlchemy resolved to a newer release inside the container whose default PostgreSQL driver differed from the one installed, so the same code worked locally and failed in the container.
- Data files and secrets are excluded by `.dockerignore`; data is mounted from `./data` and the Hugging Face model cache lives in a named volume.
- The container command runs `alembic upgrade head` before starting Gunicorn, so a fresh database gets its schema automatically.

**AWS (previous single-container version)**

The earlier version of the API was deployed and verified on EC2:

| | |
|---|---|
| Instance | t3.small (2 GB RAM), Ubuntu, 30 GB gp3, eu-central-1 |
| Firewall | Security Group restricting ports 22 and 5000 to a single source IP |
| Data | FAISS index and dataset fetched from a private S3 bucket at startup |
| Runtime | Docker image pulled from Docker Hub |

Loading the model and the FAISS index exceeded 2 GB and the container was killed with exit code 137 (OOM, no traceback). A 4 GB swap file resolved it without upgrading the instance — a pragmatic fix for a demo, not a production answer.

Deploying the full Compose stack to EC2 is the next step.

---

## CI/CD Pipeline

Every push to `main` checks out the code, authenticates with Docker Hub, builds the image, and pushes it. Defined in `.github/workflows/docker-build.yml`.

---

## Design Decisions

**Why RAG instead of fine-tuning?**
RAG allows updating the knowledge base by rebuilding the FAISS index — no retraining needed.

**Why multilingual embeddings?**
The dataset is in English while users ask in Arabic. A multilingual model maps both languages into the same vector space, enabling cross-lingual search without a translation step.

**Why query normalization before search?**
Follow-ups like "How do I treat it?" contain nothing for FAISS to match. Normalization rewrites them as standalone questions first.

**Why conversations in PostgreSQL instead of server memory?**
The first version kept history in a Python dictionary: it was lost on every restart, could not work across more than one worker, and was not tied to any user. Storing conversations in the database fixes all three, and made the sidebar possible without redesign.

**Why every query filters by `user_id`?**
Filtering by conversation id alone would let any user read another's conversation by guessing ids (IDOR). Unguessable ids are not a fix, since ids leak through logs and URLs — ownership is checked in every query instead.

**Why Nginx in front of the API?**
It serves the frontend and the API from the same origin, removing the need for CORS in the deployed stack, and it is the natural place to add HTTPS later.

**Why vanilla JavaScript?**
One page with modest state. A framework would add a build step and a dependency tree without solving a problem the project has.

---

## Known Limitations & Roadmap

- **No rate limiting on `/login`** — passwords are hashed with bcrypt, but repeated attempts are not throttled yet.
- **Tokens stored in `localStorage`** — simple, but readable by any script on the page if an XSS bug ever existed. All rendering uses `textContent` to reduce that risk; httpOnly cookies are the stronger option.
- **Access tokens cannot be revoked early** — after logout, an access token remains valid for up to 15 minutes. This is the accepted trade-off of stateless JWTs.
- **Registration reveals existing emails** (`409`) — fully hiding it needs email verification.
- **CORS is open to all origins** — needed only for opening the frontend from disk during development.
- **No automated tests yet** — the CI pipeline builds the image but does not verify behaviour. pytest in CI is next.
- **Gemini free tier** — when the daily quota is exhausted, `/ask` returns `503`.
- **No HTTPS yet** — planned with Nginx and a certificate on the deployed server.
- **Single instance** — no redundancy or autoscaling.

---

## Author

**Osama Jehad AL-Karasneh**
Computer Engineering Graduate — Yarmouk University
[LinkedIn](https://linkedin.com/in/osama-al-karasneh) • [GitHub](https://github.com/Osama-ai123)
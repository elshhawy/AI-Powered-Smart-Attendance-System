<div align="center">

# AI-Powered Smart Attendance & Institutional Intelligence Platform

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-VectorSearch-00A67E?style=for-the-badge)
![Groq](https://img.shields.io/badge/LLaMA_3-Groq_LPU-F55036?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**A biometric identity and institutional-analytics platform that fuses computer vision, vector similarity search, and generative AI into a single, multi-tenant academic operations engine.**

</div>

---

## 1. Executive Summary

The **AI-Powered Smart Attendance & Institutional Intelligence Platform** is a production-grade, multi-tenant academic operations system that replaces manual roll-calling with a fully automated, biometrically-verified attendance pipeline.

At its core, the system fuses three independent AI subsystems into a cohesive service mesh governed by strict Role-Based Access Control (RBAC) and organizational data isolation:

- A **deep-learning face detection and recognition engine** (RetinaFace + ArcFace)
- A **liveness-verification layer** to defeat presentation-attack fraud
- A **Retrieval-Augmented Generation (RAG) conversational engine** (LLaMA 3)

Rather than merely logging timestamps, the platform transforms raw camera frames into verified identity events in sub-second time and persists them as structured relational data. That data is then exposed through a natural-language interface that allows academic administrators and students alike to interrogate institutional attendance patterns conversationally, in both Arabic and English.

The result is a system that is simultaneously a **biometric security appliance**, a **real-time analytics platform**, and an **intelligent decision-support assistant** — architected end-to-end with privacy-by-design principles that guarantee raw biometric imagery is never persisted.

---

## 2. The AI Engine — System Centerpiece

The intelligence layer is the architectural core of this platform. It is deliberately decomposed into two independent, loosely-coupled pipelines that share the same data substrate but serve orthogonal purposes:

- The **Recognition Pipeline** — *who is present?*
- The **RAG Pipeline** — *what does the data mean?*

### 2.1 The Recognition Pipeline

The recognition pipeline is a four-stage cascade, implemented as a chain-of-responsibility (`RecognitionPipeline.recognize()`), where each stage must succeed before the next executes. This design fails fast, minimizes wasted compute on invalid input, and produces auditable rejection reasons at every gate.

**Stage 1 — Face Detection (RetinaFace).**
Incoming frames are passed to **RetinaFace**, a single-stage dense face detector chosen specifically for its robustness against small, non-frontal, and partially-occluded faces — conditions typical of an uncontrolled classroom camera feed rather than a studio enrollment photo.

The detector enforces a strict **single-subject invariant**: it raises a `FaceNotDetectedException` when zero faces are present and a `MultipleFacesException` when more than one face is found, preventing identity ambiguity at the source rather than downstream. A contextual margin is applied around the detected bounding box prior to cropping, which measurably improves embedding stability on the following stage.

**Stage 2 — Liveness / Anti-Spoofing Verification.**
Before any biometric matching occurs, the cropped face is passed through a **Silent-Face Anti-Spoofing** liveness classifier. This stage is architecturally non-negotiable and executes *before* embedding extraction — a deliberate ordering decision that ensures no computational resources are spent generating an identity match for content that hasn't been proven to originate from a live human subject.

**Why Liveness Detection Is Mission-Critical.**
Without a liveness gate, any biometric attendance system is trivially defeated by a **presentation attack** — holding a printed photograph, a phone screen, or a video replay of an enrolled student in front of the sensor. This is the single most common attack vector against face-based authentication in academic deployments, where enrollment photos are often publicly accessible via social media, ID cards, and course rosters.

The anti-spoofing model is trained to discriminate real from fake facial captures based on micro-textural cues that automated cameras cannot fabricate: natural skin micro-texture and specular reflection versus the flat, moiré-patterned, or screen-glow artifacts characteristic of a photograph-of-a-photograph or a screen-replay. By enforcing this check as a hard gate ahead of the embedding stage, the system architecturally guarantees that the vector search — and by extension, the entire attendance ledger — can only ever be populated by verified-live biometric events. This makes fraudulent proxy attendance, a persistent integrity problem in unmonitored academic settings, computationally infeasible rather than merely discouraged.

**Stage 3 — Facial Embedding (ArcFace / buffalo_l).**
The full frame — not the cropped face, since ArcFace performs its own internal alignment via InsightFace — is passed to **ArcFace**, using the `buffalo_l` model from the InsightFace model zoo. This model was selected as the highest-accuracy configuration in the zoo, balancing embedding dimensionality against discriminative power.

ArcFace projects the face into a **512-dimensional embedding space** using an additive angular margin loss, a formulation that explicitly maximizes inter-class angular separation while minimizing intra-class variance. This means embeddings of the *same* individual, captured under different lighting, pose, and expression conditions, cluster tightly in vector space, while embeddings of *different* individuals are pushed angularly apart. Every embedding is L2-normalized to unit length prior to persistence, which converts Euclidean distance comparisons into a numerically stable, scale-invariant proxy for cosine similarity.

**Stage 4 — Vector Similarity Search (FAISS).**
The normalized 512-dimensional embedding is queried against a **FAISS `IndexFlatL2`** vector index — an exhaustive nearest-neighbor index optimized for exact search over dense vector spaces — which returns the closest enrolled student identity and the corresponding L2 distance in a single `k=1` query.

This distance is deterministically converted to a bounded **[0.0 – 1.0] confidence score** via the formula `confidence = 1 − (distance / threshold)`, and any match exceeding the configured `SIMILARITY_THRESHOLD` is rejected rather than force-matched, eliminating false-positive identification. Because `IndexFlatL2` performs the search as a single vectorized brute-force comparison against the in-memory index, identification consistently resolves in **sub-second time**, even as the enrolled population scales — a critical property for a live, unattended kiosk workflow where multiple students may present in rapid succession.

The index and its `student_id` mapping are persisted to disk after every mutation, and the system is engineered to gracefully rebuild a corrupted or empty index at startup rather than fail the service.

```
Camera Frame
     │
     ▼
[1] RetinaFace  ──────────►  Exactly-one-face invariant enforced
     │
     ▼
[2] Silent-Face Anti-Spoof ─►  Reject presentation attacks (photo / screen / mask)
     │
     ▼
[3] ArcFace (buffalo_l) ────►  512-dim L2-normalized embedding
     │
     ▼
[4] FAISS IndexFlatL2 ──────►  Sub-second nearest-neighbor match + confidence score
     │
     ▼
Verified Identity Event → PostgreSQL Attendance Record
```

### 2.2 The RAG (Retrieval-Augmented Generation) Pipeline

The second AI subsystem is a domain-grounded conversational engine that allows administrators and students to query institutional attendance data using natural language, in either **Arabic or English**, rather than navigating static dashboards. This is deliberately engineered as a **Retrieval-Augmented Generation** architecture — not a naive LLM wrapper — precisely because a general-purpose language model has no inherent knowledge of, and cannot be trusted to hallucinate facts about, a specific institution's live student records.

**Why RAG, and not a fine-tuned or standalone model?**
A standalone LLM has no access to the organization's PostgreSQL data and would either refuse to answer institution-specific questions or, worse, fabricate plausible-sounding but false attendance statistics. The RAG architecture solves this by **grounding every generated response in facts retrieved from the live database at inference time**, guaranteeing factual consistency between what the model says and what the system of record actually contains.

The pipeline executes as a strict three-stage sequence:

1. **Retrieve** — The `ContextBuilder` component queries the `AttendanceRepository`, `StudentRepository`, and `CourseSessionRepository` directly against PostgreSQL, computing real-time aggregates: present/late/absent partitions for the current day, attendance-rate percentages, and week-over-week at-risk student identification (flagging students who have attended below a 60% threshold across the tracked period). This is a live SQL query against production data — not a static or cached snapshot.
2. **Augment** — The retrieved facts are serialized into a structured plain-text context block and injected directly into a role-specific system prompt. Two distinct prompt templates enforce **strict scope isolation**: the administrator prompt grounds responses in organization-wide data, while the student-facing prompt is architecturally restricted to that individual's own attendance record. The model is explicitly instructed to decline any question about other students or class-wide statistics, enforcing privacy at the prompt-engineering layer in addition to the API authorization layer.
3. **Generate** — The augmented prompt, together with the last ten turns of conversational history for continuity, is sent to **LLaMA 3 (70B-parameter variant)** served via **Groq's LPU inference infrastructure**, selected for its exceptionally low-latency token generation. Inference is run at a **low temperature (0.3)**, a deliberate decoding-parameter choice that biases the model toward deterministic, fact-reproducing completions over creative variation — appropriate for a system whose outputs may inform institutional decisions.

```
Admin/Student Question
        │
        ▼
ContextBuilder ──► Live SQL Query (PostgreSQL) ──► Structured Fact Block
        │
        ▼
Role-Scoped Prompt Assembly (Admin-wide vs. Student-self-only)
        │
        ▼
LLaMA 3 · Groq LPU Inference  (temperature = 0.3)
        │
        ▼
Fact-Grounded, Bilingual (AR/EN) Natural-Language Response
```

This grounding strategy directly mitigates the two dominant failure modes of production LLM deployments — **hallucination** and **stale knowledge** — by ensuring the model never answers from parametric memory alone, only from data retrieved at the moment of the query.

---

## 3. Technical Architecture

The system is implemented as a decoupled, service-oriented architecture with a clean separation between presentation, API, business-logic, AI, and data layers.

| Layer | Technology | Responsibility |
|---|---|---|
| **Frontend** | React 18 (Vite), Tailwind CSS, Zustand | Admin dashboard, student portal, live camera capture UI, chat interface |
| **API Gateway** | FastAPI (ASGI, Uvicorn) | Request validation, JWT/kiosk-key verification, routing to services |
| **Business Logic** | Python Service Layer | Orchestrates AI pipeline, database transactions, notification dispatch |
| **AI / Recognition** | RetinaFace, InsightFace (ArcFace `buffalo_l`), FAISS, OpenCV | Detection → Liveness → Embedding → Vector Search |
| **Conversational AI** | Groq-hosted LLaMA 3, custom RAG orchestration | Natural-language, fact-grounded institutional Q&A |
| **Relational Data** | PostgreSQL, SQLAlchemy ORM, Alembic migrations | Organizations, Users, Students, Courses, Attendance |
| **Vector Data** | FAISS `IndexFlatL2` (on-disk persisted index) | 512-dim biometric embeddings, keyed to `student_id` |
| **Auth** | JWT (`python-jose`), bcrypt, Google OAuth2 | Access/refresh tokens, kiosk API keys, RBAC enforcement |
| **Deployment** | Docker, Docker Compose | Containerized, reproducible multi-service orchestration |

The API layer strictly mediates *all* access to the data and AI layers. Neither the React client nor the camera kiosk ever communicates directly with PostgreSQL or the FAISS index, enforcing a single, auditable point of control for every write and read.

---

## 4. Project Structure

The repository follows a **layered, domain-oriented structure** that mirrors the architecture described above, keeping AI logic, API routing, persistence, and presentation cleanly separated.

```
.
├── docker/                        # Dockerfile(s) and Compose orchestration
├── migrations/                    # Alembic migration scripts
├── scripts/                       # Operational scripts (admin creation, seeding, DB utilities)
├── src/
│   ├── ai/                        # Recognition pipeline: detection, anti-spoofing, embedding
│   │   ├── detector.py
│   │   ├── anti_spoofing.py
│   │   ├── embedder.py
│   │   └── recognition_pipeline.py
│   ├── api/v1/endpoints/          # FastAPI routers (one module per resource)
│   │   ├── auth.py / google_auth.py
│   │   ├── students.py / student_portal.py
│   │   ├── attendance.py / courses.py
│   │   ├── organizations.py / reports.py
│   │   └── chat.py                # RAG chatbot endpoint
│   ├── core/                      # Configuration, security primitives, FAISS index wrapper
│   │   ├── config.py
│   │   ├── security.py
│   │   └── vector_index.py
│   ├── db/                        # SQLAlchemy models access via the repository pattern
│   │   └── repositories/          # One repository per aggregate (base, student, course, ...)
│   ├── llm/                       # RAG orchestration: context building, prompts, generation
│   │   ├── context_builder.py
│   │   ├── prompts.py
│   │   └── rag_pipeline.py
│   ├── models/                    # SQLAlchemy ORM entities
│   ├── schemas/                   # Pydantic request/response schemas
│   ├── services/                  # Business-logic orchestration layer
│   └── main.py                    # FastAPI application factory, router registration, CORS
├── tests/                         # Pytest suite (auth, students, attendance) with fixtures
├── view_react/                    # React 18 + Vite frontend (admin & student portals)
│   └── src/
│       ├── api/                   # Axios client and API bindings
│       ├── components/layout/     # Shared layout, sidebar, student layout shells
│       ├── pages/                 # Admin views (Dashboard, Camera, Students, Reports, ...)
│       ├── pages/student/         # Student-facing views (self-service portal)
│       └── store/                 # Zustand state management (auth store)
├── alembic.ini
├── pytest.ini
└── requirements.txt
```

The **repository pattern** (`src/db/repositories/`) decouples business logic from SQLAlchemy query construction, and every repository extends a shared `BaseRepository` to keep CRUD behavior consistent across aggregates. The **service layer** (`src/services/`) is the sole caller of repositories from the API layer, keeping endpoint handlers thin and orchestration logic testable in isolation.

---

## 5. Core Features

- **Role-Based Access Control (RBAC)** — Three-tier permission model (`super_admin`, `admin`, `student`) enforced via FastAPI dependency injection, scoping every query by role and organizational context.
- **Multi-Tenant Organization Isolation** — Students, courses, and attendance records are logically partitioned by `organization_id`; `admin` users are cryptographically bound to a single organization in their JWT claims, while `super_admin` accounts operate unrestricted across tenants.
- **Real-Time Biometric Attendance** — Sub-second face-based identification with liveness verification, invoked via an authenticated camera-kiosk endpoint.
- **Bilingual RAG Chatbot** — Fact-grounded conversational analytics for administrators and a privacy-scoped self-service assistant for students, in Arabic or English.
- **Student Self-Service Portal** — Dedicated React views for personal attendance history, weekly schedule, and profile management, authenticated independently of the admin console.
- **Course & Session Management** — Full course-session scheduling with weekday/time-slot definitions and late-arrival thresholds.
- **Dual Authentication Strategy** — Stateless JWT (access + refresh) for interactive human sessions; a static, header-based API key for unattended machine-to-machine kiosk authentication.
- **Google OAuth2 Integration** — Federated identity login alongside native credential authentication.
- **Attendance Reporting** — Aggregate and per-student analytics computed live from relational data.
- **Fully Containerized Deployment** — Reproducible, environment-isolated deployment via Docker Compose.

---

## 6. Data Security & Privacy

The platform is engineered around a **strict data-segregation model** that separates biometric material, identity metadata, and relational records into isolated storage systems, each governed by a distinct access-control mechanism.

- **Raw facial images are NEVER persisted.** At no point in the enrollment or recognition pipeline is a captured image frame or face crop written to disk or to any database table. Images exist only transiently in process memory for the duration of the detection → liveness → embedding pipeline execution, after which only the resulting **irreversible 512-dimensional mathematical embedding** is stored. This is a deliberate privacy-by-design decision: the embedding vector cannot be inverted to reconstruct a recognizable facial image, meaning a full compromise of the vector store does not constitute a leak of biometric imagery.
- **Segregated storage architecture** — Biometric embeddings live exclusively in the **FAISS vector index** (keyed only by an opaque integer `student_id`), while all personally identifiable metadata (name, enrollment date, organization) lives in **PostgreSQL**. Neither store contains information sufficient to fully reconstruct the other without an authenticated join through the API layer.
- **Credential hardening** — All user passwords are hashed with **bcrypt** (adaptive, salted hashing); plaintext credentials are never logged or persisted.
- **Token-scoped authorization** — JWT access tokens are short-lived (30 minutes) and carry `role`, `organization_id`, and `student_id` claims that are cryptographically verified server-side on every request, preventing tenant-boundary or role-escalation attacks via token tampering.
- **Machine-to-machine isolation** — The camera kiosk authenticates via a distinct, non-JWT static API key (`X-API-Key`), scoped to the attendance-marking endpoint only, ensuring an unattended device credential cannot be leveraged for administrative access even if physically compromised.
- **No public account self-registration** — Administrative accounts are provisioned exclusively via an authenticated CLI script, closing off unauthenticated account-creation as an attack surface.
- **Environment-isolated secrets** — All credentials, API keys, and connection strings are externalized to `.env` and explicitly excluded from version control.

---

## 7. System Setup Guide

### Prerequisites
- Docker & Docker Compose
- A configured `.env` file (database URL, `SECRET_KEY`, `KIOSK_API_KEY`, `GROQ_API_KEY`, Google OAuth credentials — see `.env.example`)

### Environment Variables

All runtime configuration is loaded through a Pydantic `Settings` class (`src/core/config.py`), which validates required variables at startup and fails fast if any are missing.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Signing key for JWT access/refresh tokens |
| `KIOSK_API_KEY` | Static API key for machine-to-machine kiosk authentication |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth2 federated login credentials |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL (defaults to `http://localhost:8000/api/v1/auth/google/callback`) |
| `GROQ_API_KEY` | Authentication for Groq's LPU inference infrastructure (LLaMA 3) |
| `EMAIL_FROM` / `EMAIL_APP_PASSWORD` | Outbound SMTP credentials for system notifications |
| `ADMIN_ALERT_EMAIL` | Destination address for administrative alerts |
| `FAISS_INDEX_PATH` / `FAISS_ID_MAP_PATH` | Disk locations for the persisted vector index and its `student_id` mapping |
| `SIMILARITY_THRESHOLD` | Maximum L2 distance accepted as a valid biometric match (default `0.8`) |
| `SESSION_START_HOUR` / `SESSION_START_MINUTE` | Fallback session start time when no active course session is scheduled |
| `LATE_THRESHOLD_MINUTES` | Minutes after session start before an attendance record is marked late |

### Deployment

```bash
# 1. Clone the repository
git clone <repository-url>
cd <project-directory>

# 2. Configure environment variables
cp .env.example .env
# Populate DATABASE_URL, SECRET_KEY, KIOSK_API_KEY, GROQ_API_KEY, GOOGLE_CLIENT_ID/SECRET

# 3. Build and launch the full stack (API + React frontend + PostgreSQL)
docker compose -f docker/docker-compose.yml up --build

# API available at:        http://localhost:8000
# React frontend at:       http://localhost:3000
```

### Database Migrations

```bash
# Apply all Alembic migrations to initialize the schema
alembic upgrade head
```

### Provisioning the First Administrator

```bash
python scripts/create_admin.py
```

### Seeding Demonstration Data

For evaluation and demonstration purposes, a comprehensive seeding script populates the system with realistic multi-tenant data: organizations, RBAC-scoped admins, courses with weekly session schedules, and biometrically-enrolled students. Each student is enrolled through the actual `RecognitionPipeline`, generating genuine FAISS embeddings from sample face imagery.

```bash
pip install Faker  # seeding dependency, not required at runtime
python scripts/seed_database.py
```

This script exercises the full production enrollment path — including detection, liveness verification, and FAISS indexing — rather than inserting synthetic placeholder vectors, ensuring the demonstration environment behaves identically to production.

---

## 8. Testing

The project ships with a **Pytest suite** (`tests/`) covering authentication, student management, and attendance workflows, configured via `pytest.ini` with coverage reporting enabled by default (`pytest-cov`).

Key characteristics of the test harness (`tests/conftest.py`):

- **Isolated test database** — Tests run against an in-memory SQLite engine rather than the production PostgreSQL instance, with tables created and dropped per session via SQLAlchemy's `Base.metadata`.
- **Mocked AI pipeline** — The `RecognitionPipeline` is replaced with a `MagicMock` at the application-state level, allowing the full FastAPI request lifecycle to be exercised without requiring GPU resources or downloading model weights.
- **Dependency overrides** — FastAPI's `get_db` and `verify_kiosk_key` dependencies are overridden at the app level, decoupling endpoint tests from real infrastructure while still exercising the actual routing and validation logic.
- **Session-scoped fixtures** — Shared fixtures (`client`, `auth_headers`, `test_org`) provision a authenticated test admin and organization once per test session, reducing redundant setup across test modules.

To run the full suite with coverage output:

```bash
pytest
```

---

## 9. API Documentation

The complete REST API surface is **self-documenting** via FastAPI's built-in OpenAPI (Swagger) integration. Once the backend is running, interactive, auto-generated documentation is available, including request/response schemas, authentication requirements, and live "Try it out" execution:

```
http://localhost:8000/docs
```

An alternative ReDoc-formatted reference is available at `http://localhost:8000/redoc`.

---

## 10. Development Team

> Developed under the **Digital Egypt Pioneers Initiative (DEPI)** — Managed by **EYouth** — Supervised by **Eng. Alaa Samir**

| Team Member |
|---|
| Abdelrahman Elsayed Elshhawy |
| Mohamed Khairy Eid Elzeblawy |
| Rouaa Sameh Elbadrawy |
| Farida Abdelhalim Mohamed Abdelaal |
| Wasim Ebada Mohamed Abouajaga |
| Mostafa Abdelsadek Mohamed Zayed |

---

<div align="center">

*Engineered as a demonstration of applied computer vision, vector-search infrastructure, and grounded generative AI in a secure, multi-tenant academic system.*

</div>

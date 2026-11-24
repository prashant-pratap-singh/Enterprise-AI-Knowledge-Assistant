# Implementation Tasks: Enterprise AI Knowledge Assistant

This document tracks implementation progress across all 18 development phases.

Legend:
- `[ ]` Not Started
- `[/]` In Progress
- `[x]` Completed & Verified

---

## Phase 0: Repository Inspection & Planning
- [x] Inspect existing repository, toolchain, and runtime environment.
- [x] Identify compatibility and dependency constraints (Python 3.14 host vs Python 3.12 target in Docker, Node 24).
- [x] Create `.gitignore` for Python, Node, Vite, Docker, and database files.
- [x] Create `.env.example` with comprehensive settings.
- [x] Create `ARCHITECTURE.md` with system design, Mermaid diagrams, and ER schemas.
- [x] Create `TASKS.md` implementation checklist.

## Phase 1: Project Structure & Scaffolding
- [x] Create monorepo directory layout (`backend/`, `frontend/`, `infrastructure/`, `evaluation/`, `docs/`).
- [x] Create `backend/requirements.txt` with pinned, compatible dependencies.
- [x] Create backend directory structure with `__init__.py` modules (`app/api/v1`, `core`, `db`, `schemas`, `repositories`, `services`, `ingestion`, `rag`, `evaluation`, `observability`).
- [x] Implement `backend/app/core/config.py` using Pydantic Settings.
- [x] Implement `backend/app/main.py` entry point with health and readiness routes.
- [x] Create `frontend/` scaffolding with `package.json`, `vite.config.ts`, `tsconfig.json`, `tailwind.config.js`, and `src/` modules.
- [x] Create `infrastructure/docker-compose.yml` for PostgreSQL, ChromaDB, Redis, Backend, and Frontend.
- [x] Verify Phase 1 scaffolding and execute smoke test.

## Phase 2: Database Design & Persistence Layer
- [x] Configure SQLAlchemy 2.0 async engine and session factory (`db/session.py`, `db/base.py`).
- [x] Implement relational ORM models (`User`, `Organization`, `Membership`, `Workspace`, `Document`, `DocumentChunk`, `Conversation`, `Message`, `EvaluationRun`).
- [x] Implement PostgreSQL full-text search vector (`tsvector`) and GIN indexes on `DocumentChunk`.
- [x] Setup Alembic configuration and generate initial migration script.
- [x] Write database repository classes (`user_repo`, `organization_repo`, `workspace_repo`, `document_repo`, `conversation_repo`).
- [x] Add unit tests for database models and relationships (6 passing tests in `backend/tests/test_db_models.py`).

## Phase 3: Authentication, Security & RBAC
- [x] Implement Argon2 password hashing utility with secure PBKDF2 fallback (`core/security.py`).
- [x] Implement JWT token generation, verification, and refresh logic with tamper protection.
- [x] Implement FastAPI security dependencies (`get_current_user`, `RequireRole`, `RequireWorkspaceAccess`).
- [x] Implement RBAC permissions checks (`ADMIN`, `EDITOR`, `VIEWER`).
- [x] Implement multi-tenant workspace access authorization dependency.
- [x] Create auth & organization API endpoints (`/register`, `/login`, `/refresh`, `/logout`, `/me`, `/organizations`).
- [x] Add unit and security tests for authentication and tenant isolation (5 passing tests in `backend/tests/test_auth_security.py`).

## Phase 4: Document Ingestion Pipeline
- [ ] Implement file upload validation (size, MIME type, empty/corrupt detection, safe filenames).
- [ ] Implement SHA-256 deduplication service.
- [ ] Implement document parsers:
  - [ ] PDF parser with PyMuPDF (text extraction, page mapping, OCR requirement detection).
  - [ ] DOCX parser with `python-docx` (paragraphs, tables).
  - [ ] TXT / Markdown parser.
  - [ ] CSV parser with `pandas` (row-to-entity transformation).
- [ ] Implement configurable token-based chunking with boundary and metadata preservation.
- [ ] Implement ingestion coordinator pipeline with async processing and status transitions (`uploaded` -> `processing` -> `indexed` / `failed`).
- [ ] Add unit tests for all parsers, chunking strategies, and deduplication.

## Phase 5: Embedding & Vector Database
- [ ] Implement vector store abstraction interface (`VectorStoreBase`).
- [ ] Implement ChromaDB adapter supporting both local embedded storage and HTTP client-server mode.
- [ ] Implement embedding provider abstraction supporting Google Gemini embeddings (`models/text-embedding-004`).
- [ ] Implement vector upsert, metadata filtering (`organization_id`, `workspace_id`), and vector deletion by document ID.
- [ ] Implement collection health check and reconciliation logic.
- [ ] Add unit tests for vector store operations and metadata filtering.

## Phase 6: Retrieval Engine
- [ ] Implement query preprocessing and validation.
- [ ] Implement standalone query rewriting using Gemini.
- [ ] Implement PostgreSQL Full-Text Search (lexical BM25 approximation) on chunks.
- [ ] Implement Reciprocal Rank Fusion (RRF) combining semantic and lexical ranks.
- [ ] Implement configurable reranker interface.
- [ ] Implement context budget trimmer and relevance score threshold filter.
- [ ] Implement abstention detector for weak or out-of-scope retrieval.
- [ ] Add unit tests for hybrid search, RRF scoring, and context budget management.

## Phase 7: LangGraph Multi-Agent Orchestration
- [ ] Define strongly-typed LangGraph state schema (`AgentState`).
- [ ] Implement Supervisor / Router node (query classification).
- [ ] Implement Query Understanding agent node.
- [ ] Implement Hybrid Retrieval agent node.
- [ ] Implement Evidence Analysis agent node (synthesis, contradiction detection).
- [ ] Implement Answer Generation agent node with strict citation placement.
- [ ] Implement Verification agent node (hallucination detection, citation entailment check).
- [ ] Implement Abstention node and Final Response node.
- [ ] Compile stateful graph with conditional edges and bounded retry loops.
- [ ] Add unit and integration tests for LangGraph state transitions.

## Phase 8: Citations & Source Attribution
- [ ] Implement citation parser and validator (validating `[1]`, `[2]` against retrieved chunks).
- [ ] Implement source excerpt extraction and page number mapping.
- [ ] Add anti-fabrication validator preventing non-retrieved document references.
- [ ] Add unit tests verifying citation accuracy and rejection of fabricated sources.

## Phase 9: Conversation Management
- [ ] Implement conversation and message persistence in PostgreSQL.
- [ ] Implement conversation title auto-generation from first prompt.
- [ ] Implement sliding context window manager for follow-up questions.
- [ ] Implement conversation endpoints (create, list, get history, rename, delete).
- [ ] Add unit and integration tests for conversation flows.

## Phase 10: FastAPI Endpoints
- [ ] Finalize versioned API routers under `/api/v1`:
  - [ ] Auth router (`/api/v1/auth`)
  - [ ] Organizations router (`/api/v1/organizations`)
  - [ ] Workspaces router (`/api/v1/workspaces`)
  - [ ] Documents router (`/api/v1/documents`)
  - [ ] Chat router (`/api/v1/chat` and `/api/v1/chat/stream`)
  - [ ] Evaluation router (`/api/v1/evaluation`)
  - [ ] Health and Readiness router (`/health`, `/health/ready`)
- [ ] Implement global exception handlers and standardized error responses.
- [ ] Add API integration tests using `httpx`.

## Phase 11: Frontend & Product UI
- [ ] Setup Vite + React + TypeScript + Tailwind CSS project with modern styling.
- [ ] Implement API client with Axios, token interceptors, and error handling.
- [ ] Implement Authentication screens (Login, Register).
- [ ] Implement Application Layout (Sidebar, Workspace switcher, User profile).
- [ ] Implement Dashboard with live workspace metrics.
- [ ] Implement Knowledge Base page (drag-and-drop upload, status badges, chunk inspection, delete).
- [ ] Implement Chat page (interactive chat, markdown formatting, citation markers, source side-panel).
- [ ] Implement Evaluation Dashboard page.
- [ ] Add responsive navigation and accessibility checks.

## Phase 12: Evaluation Framework
- [ ] Build synthetic evaluation dataset covering factual, multi-doc, and unanswerable queries.
- [ ] Implement deterministic retrieval metrics (Precision@K, Recall@K, MRR).
- [ ] Implement generation metrics (Faithfulness, Citation correctness, Latency, Token counts).
- [ ] Implement CLI and API evaluation runners.
- [ ] Add evaluation tests and verification benchmarks.

## Phase 13: Observability & Monitoring
- [ ] Implement structured JSON logging with request IDs and user/workspace context.
- [ ] Implement LangGraph execution tracing capturing node latencies and tokens.
- [ ] Implement health check and readiness probes.
- [ ] Ensure sensitive data masking (passwords, tokens, keys) in all logs.

## Phase 14: Performance & Reliability
- [ ] Configure database connection pooling and async query execution.
- [ ] Add bounded retry mechanisms with exponential backoff for Gemini and external calls.
- [ ] Enforce upload size limits, timeouts, and pagination across all list endpoints.

## Phase 15: Docker & Deployment
- [ ] Write optimized multi-stage `Dockerfile` for Backend.
- [ ] Write optimized multi-stage `Dockerfile` for Frontend (Nginx static serving).
- [ ] Finalize `docker-compose.yml` linking Postgres, ChromaDB, Redis, Backend, Frontend.
- [ ] Prepare Google Cloud Run configuration and deployment documentation.

## Phase 16: Comprehensive Testing
- [ ] Run backend unit tests.
- [ ] Run backend integration tests.
- [ ] Run multi-tenant security isolation tests (cross-tenant retrieval denial).
- [ ] Run end-to-end user journey tests.

## Phase 17: Documentation
- [ ] Write comprehensive `README.md` with setup guide, architecture diagrams, and API docs.
- [ ] Write `docs/DEPLOYMENT.md` for Cloud Run and production secrets.
- [ ] Write `docs/EVALUATION.md` explaining evaluation methodology and reproduction steps.

## Phase 18: Final Quality Gate
- [ ] Audit code for zero hardcoded secrets or mock responses.
- [ ] Run all automated test suites and ensure all pass.
- [ ] Verify clean, reproducible application startup.

# System Architecture

## 🏗️ High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Interface Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  Streamlit UI (Port 8501)                                       │
│  - CV Upload Interface                                          │
│  - HR Query & Chat                                              │
│  - Candidate Browser & Analytics                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP/REST
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                  API & Backend Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI (Port 8000)                                            │
│  ├─ POST /upload         → File Upload Handler                  │
│  ├─ GET /task/{id}       → Async Task Tracker                   │
│  ├─ POST /query          → LangChain Agent Router               │
│  ├─ GET /candidates      → Candidate Database Query             │
│  └─ POST /compare        → Comparison Pipeline                  │
│                                                                 │
│  Agent Orchestration                                            │
│  ├─ LLM Client (ChatOllama)                                     │
│  ├─ Tool Registry (search, compare, list)                       │
│  └─ ReAct Agent with Function Calling                           │
└──────────────────┬──────────────────────────┬──────────────────┘
                   │                          │
          Async    │                          │ Vector
          Queue    │                          │ Search
                   ▼                          ▼
┌──────────────────┐                  ┌──────────────────┐
│  Celery Worker   │                  │   ChromaDB       │
│  (Process CVs)   │                  │  Vector Store    │
│                  │                  │  Port: (embed)   │
│  - Extract text  │                  │                  │
│  - Parse fields  │                  │  Collections:    │
│  - Chunk & embed │                  │  - candidates    │
└─────────┬────────┘                  └────────┬─────────┘
          │                                    │
    Redis │ (Queue)                    Ollama  │ (Embeddings)
    Store │                            LLM API │
          │                                    │
          ▼                                    ▼
┌──────────────────┐                  ┌──────────────────┐
│      Redis       │                  │     Ollama       │
│   (Port 6379)    │                  │   (Port 11434)   │
│                  │                  │                  │
│  - Task Queue    │                  │  Models:         │
│  - Results Store │                  │  - llama3.1      │
│  - Metadata      │                  │  - nomic-embed   │
└──────────────────┘                  └──────────────────┘

      Data Persistence Layer
      ├─ ./data/uploads       (Temp CV files)
      ├─ ./data/vector_db     (ChromaDB persists)
      ├─ ./data/logs          (Application logs)
      └─ ollama_data volume   (Model cache)
```

---

## 📊 Data Flow Sequences

### 1. CV Upload & Processing

```
User (Streamlit)
    │
    ├─→ Select CV file (PDF/DOCX)
    │
    ▼
FastAPI /upload
    │
    ├─→ Validate file type
    ├─→ Save to ./data/uploads
    ├─→ Generate candidate_id (UUID)
    ├─→ Queue async task via Celery
    │
    ▼
Redis Queue
    │
    ├─→ Celery Worker picks up task
    │
    ▼
CV Processing Pipeline
    │
    ├─→ extract_text() [PDF/DOCX parser]
    ├─→ clean_text() [normalize whitespace]
    ├─→ extract_structured_metadata() [LLM-assisted extraction]
    ├─→ chunk_text() [semantic chunking]
    │
    ▼
Vector Store Addition
    │
    ├─→ Convert chunks to embeddings (Ollama nomic-embed-text)
    ├─→ Store in ChromaDB with metadata
    ├─→ Update task status to SUCCESS
    │
    ▼
Task Completion
    │
    └─→ User polls /task/{id} → gets SUCCESS + metadata
        Can now query candidates
```

### 2. HR Query & Agent Invocation

```
User (Streamlit)
    │
    └─→ "Who is best for Senior Python Engineer with AWS?"
        │
        ▼
    FastAPI /query
        │
        ├─→ Validate query length
        ├─→ Route to LangChain Agent
        │
        ▼
    HR Agent (ReAct + Tool Calling)
        │
        ├─→ LLM Router: "Which tool should I call?"
        │
        ├─→ Agent decides: "search_candidate" or "compare_candidates"
        │
        ▼
    Invoke Tool
        │
        ├─→ search_candidate("Senior Python Engineer AWS")
        │
        ▼
    Vector Search (ChromaDB)
        │
        ├─→ Embed query using Ollama embeddings
        ├─→ Similarity search with cosine distance
        ├─→ Deduplicate by candidate_id
        ├─→ Sort by relevance_score
        │
        ▼
    Return Results to Agent
        │
        ├─→ Top 5 candidates with scores
        ├─→ Skills, experience, metadata
        │
        ▼
    LLM Post-Processing
        │
        ├─→ Format response as QueryResponse
        ├─→ Validate Pydantic schema
        ├─→ Include reasoning chain
        │
        ▼
    Return to UI
        │
        └─→ Structured results + human-readable analysis
```

### 3. Candidate Comparison

```
User Request
    │
    └─→ "Compare 3 candidates for Data Science role"
        │
        ▼
    compare_candidates Tool
        │
        ├─→ Search vector store for "Data Science"
        ├─→ Return top 3 candidates
        ├─→ Sort by relevance score
        │
        ▼
    Format Comparison Results
        │
        ├─→ Create rank ordering
        ├─→ Include scoring/justification
        ├─→ Highlight skill matches
        │
        ▼
    Return ComparisonResult
        │
        └─→ {"candidates": [...], "ranked": [...], "summary": "..."}
```

---

## 🔧 Component Details

### FastAPI Backend (`app/main.py`)

**Responsibilities:**
- HTTP request/response handling
- File upload management
- Async task orchestration
- CORS & middleware setup
- Health checking

**Key Endpoints:**
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /upload | Upload CV, trigger async processing |
| GET | /task/{id} | Check async task status |
| POST | /query | Invoke HR agent with question |
| POST | /compare | Compare candidates |
| GET | /candidates | List all candidates |
| DELETE | /candidates/{id} | Remove candidate |
| POST | /reset | Clear database |
| GET | /health | Service health check |

### CV Processor (`app/cv_processor.py`)

**Responsibilities:**
- PDF/DOCX text extraction
- Metadata extraction (name, email, skills, years_exp)
- Text normalization & cleaning
- Semantic chunking (800 char chunks, 100 char overlap)

**Processing Pipeline:**
```
Raw File
  ├─ PDF/DOCX Parser (extract_text)
  ├─ Text Cleaner (clean_text) - normalize whitespace
  ├─ Metadata Extractor (extract_structured_metadata)
  │  ├─ Regex: email, phone
  │  ├─ Pattern match: years of experience
  │  ├─ Keyword matching: skills (80+ tech keywords)
  │  └─ Pydantic validation
  ├─ Text Chunker (chunk_text)
  │  └─ Sliding window: 800 chars, 100 char overlap
  └─ Return: (text, metadata, chunks)
```

### Vector Store (`app/vector_store.py`)

**Responsibilities:**
- ChromaDB wrapper for semantic search
- Embedding generation via Ollama
- Candidate metadata indexing
- CRUD operations

**Key Methods:**
- `add_cv(candidate_id, text, chunks, metadata)` - Add CV to store
- `search(query, k=5)` - Semantic similarity search
- `get_all_candidates()` - List candidates
- `delete_candidate(candidate_id)` - Remove candidate
- `clear_all()` - Reset database

**Storage Structure:**
```
ChromaDB Collection: "candidates"
├─ Document IDs: candidate_id + chunk_index
├─ Content: Text chunks (800 chars)
├─ Embeddings: nomic-embed-text vectors (768-dim)
└─ Metadata:
   ├─ candidate_id
   ├─ name, email, skills
   ├─ years_experience
   └─ chunk_index
```

### LangChain Agent (`app/agent.py`)

**Responsibilities:**
- Tool registration & routing
- LLM invocation with function calling
- Error handling & retry logic
- Response validation & formatting

**Agent Type:** ReAct (Reasoning + Acting)

**Tool Registry:**
1. `search_candidate(query, top_k)` - Find matching candidates
2. `compare_candidates(criteria, top_k)` - Compare & rank candidates
3. `get_candidate_details(candidate_id)` - Get full profile
4. `list_all_candidates()` - Get all candidates

**Agent Flow:**
```
Input Question
  ├─ LLM Routing: "Which tool should I use?"
  ├─ Tool Calling: Invoke selected tool
  ├─ Tool Execution: Run tool, get results
  ├─ Observation: Process results
  ├─ Reasoning: Synthesize analysis
  └─ Output: QueryResponse with structured results
```

### Async Task Queue (Celery + Redis)

**Responsibilities:**
- Background CV processing
- Task status tracking
- Result persistence

**Tasks:**
- `process_cv_async(filepath, candidate_id)` - Process uploaded CV
- `compare_candidates_async(criteria, top_k)` - Async comparison

**Task States:**
```
PENDING → PROGRESS → SUCCESS
              └→ FAILURE
```

**Worker Configuration:**
- Max concurrent tasks: 1 per worker
- Task timeout: 30 minutes
- Soft timeout: 25 minutes
- Prefetch: 1 task per worker

---

## 🔐 Security & Performance

### Security Measures
- File type validation (PDF/DOCX only)
- File size limits (50MB default)
- CORS configuration for API access
- Input validation (Pydantic)
- Error handling (no sensitive data in errors)

### Performance Optimizations
- Async task processing (non-blocking uploads)
- Vector database caching (ChromaDB in-memory + disk)
- Embedding caching (Ollama caches embeddings)
- Connection pooling (Redis, Ollama)
- Lazy loading (models loaded on-demand)

### Scalability Path
| Scale | Recommendation |
|-------|-----------------|
| <10k CVs | Current ChromaDB setup ✅ |
| 10k-100k | Add PostgreSQL for metadata, use Weaviate |
| 100k+ | Distributed: Redis cluster, Kubernetes |
| Multi-tenant | Add PostgreSQL with row-level security |

---

## 📦 External Dependencies

| Service | Purpose | Port | Status Check |
|---------|---------|------|--------------|
| **Ollama** | LLM inference + embeddings | 11434 | `/api/tags` |
| **Redis** | Task queue + cache | 6379 | `PING` |
| **ChromaDB** | Vector store | Embedded | Persistence check |
| **Celery** | Async worker | Internal | Task state API |

---

## 🗂️ File Organization

```
cv-reader-agent-pipeline/
├── app/
│   ├── main.py              # FastAPI app + routes
│   ├── agent.py             # LangChain agent orchestrator
│   ├── llm.py               # Ollama LLM client
│   ├── tools.py             # HR tools (search, compare, etc.)
│   ├── cv_processor.py      # PDF/DOCX extraction
│   ├── vector_store.py      # ChromaDB wrapper
│   ├── schemas.py           # Pydantic models
│   ├── config.py            # Settings management
│   ├── logger.py            # Structured logging
│   ├── celery_app.py        # Celery initialization
│   ├── tasks.py             # Async tasks
│   └── __init__.py
├── ui/
│   └── app.py               # Streamlit dashboard
├── tests/
│   ├── test_cv_processor.py
│   ├── test_vector_store.py
│   ├── test_agent.py
│   ├── test_e2e.py
│   └── __init__.py
├── data/
│   ├── uploads/             # Temp CV files
│   ├── vector_db/           # ChromaDB persistence
│   ├── logs/                # Application logs
│   └── sample_cvs/          # Test data
├── docker-compose.yml       # Service orchestration
├── Dockerfile               # FastAPI container
├── Dockerfile.streamlit     # Streamlit container
├── requirements.txt         # Python dependencies
├── .env.example             # Configuration template
├── run.sh / run.bat         # Startup scripts
├── QUICKSTART.md            # Quick start guide
├── ARCHITECTURE.md          # This file
└── API.md                   # API reference
```

---

## 🚀 Deployment Considerations

### Development
- Single machine with Docker Compose
- In-memory Celery for testing
- SQLite-style vector store

### Production
- Kubernetes orchestration
- Dedicated task workers (Celery)
- PostgreSQL for metadata
- Redis cluster for caching
- Weaviate/Milvus for vector store
- Load balancing (Nginx)
- Monitoring (Prometheus + Grafana)
- Logging aggregation (ELK stack)

---

## 📈 Monitoring & Observability

### Logging
- Structured JSON logs to `./data/logs/cv-reader.log`
- Request tracking with unique IDs
- Tool invocation logging
- Error tracing with stack traces

### Metrics
- Task count (queued, processing, completed)
- Vector store size (number of candidates)
- Query latency
- Tool usage statistics

### Health Checks
```bash
GET /health
# Returns service status for: ollama, redis, vector_db
```

---

**See [API.md](API.md) for endpoint documentation and [QUICKSTART.md](QUICKSTART.md) for usage guide.**

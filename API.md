# API Reference - CV Reader Agent Pipeline

## Base URL
```
http://localhost:8000
```

## Interactive Documentation
```
http://localhost:8000/docs       (Swagger UI)
http://localhost:8000/redoc      (ReDoc)
```

---

## Authentication
Currently no authentication required. In production, add JWT bearer token auth.

---

## Endpoints

### Health & Status

#### GET /health
Check service health and connected services status.

**Response:**
```json
{
  "status": "running",
  "version": "1.0.0",
  "services": {
    "ollama": "ok",
    "redis": "ok",
    "vector_db": "ok"
  }
}
```

**Status Codes:** 200

---

### CV Upload & Processing

#### POST /upload
Upload a CV file (PDF or DOCX) for async processing.

**Request:**
```
Content-Type: multipart/form-data

file: <binary> (PDF or DOCX, max 50MB)
```

**Response:** 200
```json
{
  "status": "queued",
  "candidate_id": "abc12345",
  "task_id": "task-uuid-here",
  "filename": "resume.pdf",
  "message": "CV processing started. Use task_id ... to check status."
}
```

**Error Responses:**
- 400: Invalid file format (not PDF/DOCX)
- 400: File too large (>50MB)
- 500: Server error during upload

**Example:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@resume.pdf"
```

---

#### GET /task/{task_id}
Check the status of an async CV processing task.

**Parameters:**
- `task_id` (path): Task ID from /upload response

**Response:** 200
```json
{
  "task_id": "task-uuid",
  "status": "SUCCESS",
  "progress": 100,
  "metadata": {
    "candidate_id": "abc12345",
    "name": "John Doe",
    "email": "john@example.com",
    "years_experience": 5,
    "skills": ["Python", "AWS", "FastAPI"]
  },
  "error": null
}
```

**Task Status Values:**
- `PENDING` - Waiting in queue
- `PROCESSING` - Currently being processed
- `SUCCESS` - Completed successfully
- `FAILED` - Processing failed

**Progress:** 0-100 (percentage)

**Error Responses:**
- 404: Task not found
- 500: Server error

**Example:**
```bash
curl http://localhost:8000/task/task-uuid-here
```

---

### HR Queries & Analysis

#### POST /query
Send a question to the HR agent. Agent will invoke appropriate tools and return analysis.

**Request:**
```json
{
  "question": "Who is the best fit for Senior Python Backend Engineer with AWS?",
  "top_k": 5
}
```

**Parameters:**
- `question` (required): HR question or task (5-1000 chars)
- `top_k` (optional): Number of top results to consider (1-20, default: 5)

**Response:** 200
```json
{
  "query": "Who is the best fit for Senior Python Backend Engineer with AWS?",
  "tool_used": "search_candidate",
  "candidates_found": 3,
  "structured_results": [
    {
      "candidate_id": "abc12345",
      "relevance_score": 0.92,
      "matched_criteria": ["Python", "AWS", "5+ years"],
      "evidence": "Extensive Python and AWS experience documented...",
      "metadata": {
        "candidate_id": "abc12345",
        "name": "John Doe",
        "email": "john@example.com",
        "years_experience": 5,
        "skills": ["Python", "AWS", "FastAPI", "Docker", "Kubernetes"]
      }
    }
  ],
  "answer": "Based on my analysis, John Doe [abc12345] is the best fit...",
  "reasoning": "- Used search_candidate: {...}"
}
```

**Response Fields:**
- `query` - The question asked
- `tool_used` - Which tool agent invoked (search_candidate, compare_candidates, etc.)
- `candidates_found` - Number of matching candidates
- `structured_results` - Array of CandidateMatch objects with relevance scores
- `answer` - Human-readable analysis
- `reasoning` - Agent's reasoning chain

**Error Responses:**
- 400: Invalid question (too short/long)
- 500: LLM or vector store error

**Example:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Best candidates for Senior Python Engineer with AWS?",
    "top_k": 5
  }'
```

---

#### POST /compare
Compare multiple candidates based on criteria.

**Request:**
```json
{
  "criteria": "Data Science role with 3+ years ML experience",
  "top_k": 3
}
```

**Parameters:**
- `criteria` (required): Comparison criteria (5-1000 chars)
- `top_k` (optional): Number of candidates to compare (2-10, default: 3)

**Response:** 200
```json
{
  "status": "ok",
  "criteria": "Data Science role with 3+ years ML experience",
  "candidates_found": 3,
  "results": [
    {
      "candidate_id": "abc12345",
      "relevance_score": 0.95,
      "matched_criteria": ["Machine Learning", "TensorFlow", "3+ years"],
      "evidence": "Published ML research, 5 years industry experience...",
      "metadata": {...}
    }
  ],
  "summary": "Ranking: 1. John [abc12345] (95%), 2. Jane [def67890] (87%)..."
}
```

**Error Responses:**
- 400: Invalid criteria
- 404: Need at least 2 candidates in database
- 500: Server error

**Example:**
```bash
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{
    "criteria": "Data Science with ML experience",
    "top_k": 3
  }'
```

---

### Candidate Management

#### GET /candidates
List all candidates in the vector store.

**Response:** 200
```json
{
  "status": "ok",
  "total_candidates": 5,
  "candidates": [
    {
      "candidate_id": "abc12345",
      "name": "John Doe",
      "email": "john@example.com",
      "years_experience": 5,
      "skills": ["Python", "AWS", "FastAPI", "Docker", "Kubernetes"]
    }
  ]
}
```

**Error Responses:**
- 500: Vector store access error

**Example:**
```bash
curl http://localhost:8000/candidates
```

---

#### DELETE /candidates/{candidate_id}
Remove a candidate from the vector store.

**Parameters:**
- `candidate_id` (path): Candidate ID to delete

**Response:** 200
```json
{
  "status": "ok",
  "message": "Candidate abc12345 deleted"
}
```

**Error Responses:**
- 404: Candidate not found
- 500: Server error

**Example:**
```bash
curl -X DELETE http://localhost:8000/candidates/abc12345
```

---

### Database Management

#### POST /reset
Clear entire vector database (development only).

**Response:** 200
```json
{
  "status": "ok",
  "message": "Vector database reset successfully"
}
```

**Warning:** This deletes ALL candidates. Use only in development!

**Error Responses:**
- 500: Reset failed

**Example:**
```bash
curl -X POST http://localhost:8000/reset
```

---

## Response Models

### CandidateMatch
```python
{
  "candidate_id": str,           # Unique candidate ID
  "relevance_score": float,      # 0.0-1.0 matching score
  "matched_criteria": [str],     # Matched skills/requirements
  "evidence": str,               # Supporting text from CV
  "metadata": {
    "candidate_id": str,
    "name": str,
    "email": str,
    "years_experience": int,
    "skills": [str]
  }
}
```

### QueryResponse
```python
{
  "query": str,                       # Original question
  "tool_used": str,                   # Tool invoked
  "candidates_found": int,            # Count of matches
  "structured_results": [CandidateMatch],  # Detailed matches
  "answer": str,                      # Human-readable response
  "reasoning": str                    # Agent reasoning chain
}
```

### UploadResponse
```python
{
  "status": str,                 # "queued", "processing", "success"
  "candidate_id": str,           # Unique candidate ID
  "task_id": str,                # Task ID for status tracking
  "filename": str,               # Original filename
  "message": str                 # Status message
}
```

### TaskResponse
```python
{
  "task_id": str,                # Task ID
  "status": str,                 # PENDING, PROCESSING, SUCCESS, FAILED
  "progress": int,               # 0-100
  "metadata": {                  # CV metadata when completed
    "candidate_id": str,
    "name": str,
    "email": str,
    "years_experience": int,
    "skills": [str]
  },
  "error": str                   # Error message if failed
}
```

### HealthResponse
```python
{
  "status": str,                 # "running"
  "version": str,                # "1.0.0"
  "services": {
    "ollama": str,               # "ok", "offline", "error"
    "redis": str,
    "vector_db": str
  }
}
```

---

## Error Handling

All endpoints return errors in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Error Codes:**
- `400 Bad Request` - Invalid input (bad file type, malformed JSON, etc.)
- `404 Not Found` - Resource not found (candidate, task, etc.)
- `500 Internal Server Error` - Server-side error (LLM timeout, vector DB error, etc.)

**Example:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.txt"

# Response 400:
{
  "detail": "Only PDF and DOCX files are supported"
}
```

---

## Rate Limiting
Currently no rate limiting. In production:
- 10 uploads/min per IP
- 20 queries/min per IP
- Use Redis for rate limiting

---

## Timeout Configuration
- Upload: 30s
- Query: 60s
- Task check: 10s
- Vector search: 30s
- LLM inference: 60s (configurable in .env)

---

## Pagination
Not yet implemented. All results return all matches. Recommended pagination for >1000 candidates.

---

## Versioning
API version: `1.0.0`
- Breaking changes will increment major version
- New features will increment minor version

---

## Example Workflow

### 1. Upload 3 CVs
```bash
curl -X POST http://localhost:8000/upload -F "file=@cv1.pdf"
curl -X POST http://localhost:8000/upload -F "file=@cv2.pdf"
curl -X POST http://localhost:8000/upload -F "file=@cv3.docx"
# Each returns: task_id, candidate_id
```

### 2. Wait for Processing
```bash
curl http://localhost:8000/task/task-uuid-1
# Poll every 2s until status = "SUCCESS"
```

### 3. Query Candidates
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Senior Python engineer?", "top_k": 3}'
# Returns structured matches with scores
```

### 4. Compare Best Candidates
```bash
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{"criteria": "Senior Backend Engineer", "top_k": 2}'
# Returns ranked comparison
```

### 5. View All Candidates
```bash
curl http://localhost:8000/candidates
# Lists all 3 candidates
```

---

## Performance Tips

1. **Reduce top_k** for faster queries (default 5 is good)
2. **Batch uploads** - upload 5+ CVs for better performance
3. **Reuse connections** - keep HTTP connections alive
4. **Cache results** - agent responses are deterministic
5. **Monitor Ollama** - first query takes longer (warm-up)

---

**Need help?** Check [QUICKSTART.md](QUICKSTART.md) and [ARCHITECTURE.md](ARCHITECTURE.md)

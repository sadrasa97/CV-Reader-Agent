# CV Reader Agent Pipeline

> **Production-ready end-to-end CV analysis platform with LangChain Agent, Ollama LLM, ChromaDB semantic search, and Streamlit UI**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🎯 Overview

A fully containerized, production-ready CV analysis pipeline that enables HR teams to:
- **Upload** CVs (PDF/DOCX) with automatic async processing
- **Query** an AI agent to find candidates matching specific roles
- **Compare** candidates side-by-side with structured scoring
- **Manage** candidate database with semantic search

## ✨ Key Features

- 🤖 **LangChain ReAct Agent** with native tool calling for intelligent candidate analysis
- 🧠 **Local LLM** (Ollama) with llama3.1 - privacy-preserving, no API costs
- 📊 **Semantic Search** using ChromaDB vector store for intelligent matching
- ⚡ **Async Processing** with Celery + Redis for scalable CV uploads
- 📱 **Streamlit UI** with interactive dashboard for HR teams
- 🔧 **Structured Outputs** with Pydantic validation
- 🐳 **Docker Compose** orchestration - single command to run entire stack
- 📈 **Extensible** architecture ready for production enhancements

## 🏗️ Architecture

```
Streamlit UI → FastAPI Backend → LangChain Agent → Ollama LLM
                                      ↓
                              ChromaDB Vector Store
                         (Semantic Search + Metadata)
                                      ↓
                         Celery Worker + Redis Queue
                         (Async CV Processing)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- 8GB RAM (16GB recommended)
- 50GB free disk space

### Installation

```bash
# Clone repository
git clone <repo-url>
cd cv-reader-agent-pipeline

# Copy environment file
cp .env.example .env

# Start all services
./run.sh          # Linux/Mac
# or
run.bat           # Windows
```

The application will be available at:
- **Web UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

See [QUICKSTART.md](QUICKSTART.md) for detailed setup guide.

## 📖 Usage

### 1. Upload CVs
- Navigate to **📤 Upload CVs** tab
- Select one or multiple PDF/DOCX files
- Wait for async processing to complete
- Files are parsed, chunked, and embedded automatically

### 2. Query the Agent
- Go to **💬 Query Agent** tab
- Ask natural language questions:
  ```
  "Find Senior Python engineers with AWS experience"
  "Compare candidates for Data Science role"
  "Who has DevOps and Kubernetes expertise?"
  ```
- Agent automatically selects and invokes appropriate tools
- Get structured results with relevance scores

### 3. Review Results
- See matched candidates with relevance scores
- View detailed candidate profiles
- Check agent reasoning chain
- Compare candidates side-by-side

### 4. Manage Candidates
- View all candidates in database
- Delete candidates as needed
- Reset database for fresh start

## 🔌 API Endpoints

All endpoints documented in [API.md](API.md)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/upload` | Upload CV for processing |
| GET | `/task/{id}` | Check async task status |
| POST | `/query` | Query HR agent |
| POST | `/compare` | Compare candidates |
| GET | `/candidates` | List all candidates |
| DELETE | `/candidates/{id}` | Remove candidate |
| GET | `/health` | Service health check |

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain** - Agent orchestration + function calling
- **Ollama** - Local LLM (llama3.1, nomic-embed-text)
- **ChromaDB** - Vector database for semantic search
- **Celery** - Distributed task queue
- **Redis** - Message broker + caching
- **Pydantic** - Data validation

### Frontend
- **Streamlit** - Interactive web UI
- **Requests** - HTTP client

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Python 3.11** - Runtime

## 📁 Project Structure

```
cv-reader-agent-pipeline/
├── app/
│   ├── main.py              # FastAPI routes
│   ├── agent.py             # LangChain agent
│   ├── llm.py               # Ollama LLM client
│   ├── tools.py             # HR tools (search, compare)
│   ├── cv_processor.py      # PDF/DOCX extraction
│   ├── vector_store.py      # ChromaDB wrapper
│   ├── schemas.py           # Pydantic models
│   ├── config.py            # Settings
│   ├── logger.py            # Logging setup
│   ├── celery_app.py        # Celery config
│   └── tasks.py             # Async tasks
├── ui/
│   └── app.py               # Streamlit dashboard
├── tests/
│   ├── test_cv_processor.py
│   ├── test_vector_store.py
│   ├── test_agent.py
│   └── test_e2e.py
├── data/                    # Auto-created
│   ├── uploads/
│   ├── vector_db/
│   └── logs/
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.streamlit
├── requirements.txt
├── .env.example
├── QUICKSTART.md
├── ARCHITECTURE.md
├── API.md
└── README.md
```

## 🤖 How It Works

### Tool Calling Flow

When you query "Who is best for Senior Python Engineer?":

1. **Agent Router**: LLM decides which tool to call
2. **Tool Selection**: Invokes `search_candidate` tool
3. **Vector Search**: Queries ChromaDB for matching candidates
4. **Ranking**: Scores by relevance (0-1)
5. **Post-Processing**: Formats response as Pydantic model
6. **Response**: Returns structured results with evidence

### Async CV Processing

1. **Upload**: File validated, saved temporarily
2. **Queue**: Task added to Redis queue
3. **Worker**: Celery picks up task
4. **Processing**:
   - Extract text (PDF/DOCX parser)
   - Clean & normalize
   - Extract metadata (skills, experience, email)
   - Create semantic chunks
   - Generate embeddings (Ollama)
5. **Store**: Add to ChromaDB with metadata
6. **Complete**: Status updated, file cleaned up

## ⚙️ Configuration

Edit `.env` to customize:

```env
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_EMBED_MODEL=nomic-embed-text

# LLM Parameters
LLM_TEMPERATURE=0                  # Exact answers
LLM_MAX_TOKENS=2048
LLM_TIMEOUT=60                     # seconds

# Vector Store
VECTOR_DB_PATH=./data/vector_db
MAX_FILE_SIZE_MB=50

# Feature Flags
ENABLE_STRUCTURED_OUTPUT=true
```

See `.env.example` for all options.

## 🔍 Example Queries

```
"Find Python developers with 5+ years AWS experience"
"Compare top 3 candidates for Data Science role"
"Who has DevOps, Kubernetes, and infrastructure skills?"
"Show me Full Stack engineers with React and Node.js"
"Find candidates suitable for Product Manager position"
```

## 📊 Performance

- **CV Upload**: ~5-10 seconds (async, non-blocking)
- **Query**: ~2-5 seconds (LLM inference)
- **Vector Search**: <100ms (ChromaDB)
- **First Query**: ~10-15 seconds (LLM warm-up)

## 🧪 Testing

Run unit and integration tests:

```bash
# Inside Docker or virtual environment
pytest tests/ -v --cov=app/

# Specific test file
pytest tests/test_agent.py -v
```

See [tests/](tests/) directory for examples.

## 🚀 Production Deployment

### Recommended Changes

1. **Authentication**: Add JWT bearer token auth
2. **Database**: Use PostgreSQL for metadata
3. **Vector Store**: Scale to Weaviate/Milvus for >10k CVs
4. **Task Queue**: Scale Celery workers independently
5. **Monitoring**: Integrate Prometheus + Grafana
6. **Logging**: Use ELK stack for log aggregation
7. **Caching**: Add Redis caching layer
8. **Rate Limiting**: Implement per-IP limits
9. **Security**: HTTPS, input sanitization, rate limiting
10. **Load Balancer**: Nginx for multiple FastAPI instances

See [ARCHITECTURE.md](ARCHITECTURE.md) for scalability details.

## 🐛 Troubleshooting

### Ollama connection error
```bash
# Wait for Ollama to start (can take 2-5 minutes)
# Check if models are pulled
curl http://localhost:11434/api/tags
```

### Services won't start
```bash
# Check ports (8000, 8501, 11434, 6379)
docker-compose down -v
docker-compose up --build
```

### Out of memory
- Use `qwen2.5-7b` instead of `llama3.1`
- Increase Docker memory allocation
- Close other applications

See [QUICKSTART.md](QUICKSTART.md#-troubleshooting) for more help.

## 📝 Logging

Logs available at:
```
./data/logs/cv-reader.log        # Application logs
docker-compose logs -f fastapi   # FastAPI container logs
docker-compose logs -f ollama    # Ollama logs
```

## 🔐 Security

- ✅ File type validation (PDF/DOCX only)
- ✅ File size limits (50MB default)
- ✅ Input validation (Pydantic)
- ✅ Local LLM (no API keys exposed)
- ✅ CORS configured
- ⚠️ **Note**: No authentication in v1.0. Add in production.

## 📖 Documentation

- [QUICKSTART.md](QUICKSTART.md) - Setup & basic usage
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design & data flow
- [API.md](API.md) - Endpoint reference
- Code comments - Inline documentation

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Multi-language support
- Advanced ranking algorithms
- Custom skill extraction
- Dashboard enhancements
- Performance optimizations
- Additional LLM models

## 📄 License

MIT License - see LICENSE file

## ⭐ Acknowledgments

Built with:
- FastAPI
- LangChain
- ChromaDB
- Ollama
- Streamlit
- Celery
- Redis

## 📞 Support

For issues, questions, or feature requests:
1. Check [QUICKSTART.md](QUICKSTART.md) troubleshooting
2. Review logs in `./data/logs/`
3. Check [API.md](API.md) for endpoint issues
4. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system understanding

---

**Ready to get started?** → [QUICKSTART.md](QUICKSTART.md)

**Want to understand the system?** → [ARCHITECTURE.md](ARCHITECTURE.md)

**Need API reference?** → [API.md](API.md)

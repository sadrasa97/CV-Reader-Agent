# Quick Start Guide - CV Reader Agent Pipeline

## 📋 Prerequisites

1. **Docker & Docker Compose** installed
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes both)

2. **System Requirements**
   - 8GB RAM minimum (16GB recommended for Ollama)
   - 50GB free disk space (for Ollama models)
   - Modern CPU

## 🚀 Getting Started

### 1. Clone and Setup

```bash
cd cv-reader-agent-pipeline
cp .env.example .env
```

### 2. Start Services

**On Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

**On Windows:**
```bash
run.bat
```

Or manually:
```bash
docker-compose up --build
```

### 3. Wait for Services to Boot

- **Ollama** starts first (pulls models if first time)
  - Expected time: 2-5 minutes (depends on model size)
  - Models: `llama3.1` (~45GB), `nomic-embed-text` (~300MB)

- Services are healthy when:
  ```
  fastapi        | Application startup complete
  streamlit      | You can now view your Streamlit app in your browser
  ```

### 4. Access the Application

- **Web UI:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 📖 Basic Workflow

### Step 1: Upload CVs

1. Go to **"📤 Upload CVs"** tab
2. Click "Choose CV files"
3. Select PDF or DOCX files
4. Wait for processing to complete (see progress bar)
5. Files are processed asynchronously and added to the vector store

### Step 2: Query the Agent

1. Go to **"💬 Query Agent"** tab
2. Ask a question about candidates:
   ```
   "Who is the best fit for Senior Python Backend Engineer with AWS?"
   ```
   or
   ```
   "Compare candidates for Data Science role"
   ```
3. Adjust "Top K results" slider if needed
4. Click "🔍 Analyze"
5. Wait for agent to call tools and analyze

### Step 3: Review Results

- **Candidates Found:** Number of matching candidates
- **Tool Used:** Which function the agent called (search_candidate, compare_candidates, etc.)
- **Analysis:** Structured recommendations with evidence
- **Matches:** Detailed card for each candidate with score

### Step 4: Manage Candidates

Go to **"👥 Candidates"** tab to:
- View all candidates in database
- See CV metadata (name, email, skills, experience)
- Delete individual candidates
- Track database size

## 🔍 Example Queries

```
"Find me Python developers with 5+ years experience"
"Compare candidates for Product Manager role"
"Who has AWS and Kubernetes expertise?"
"Show candidates with Data Science and TensorFlow skills"
"Find candidates suitable for DevOps Engineer position"
```

## 📊 Monitor Progress

- **Active Tasks:** See processing status with progress bars
- **Analytics Tab:** View pipeline metrics and query history
- **Settings Tab:** Test API connection and clear database

## 🆘 Troubleshooting

### Services won't start

```bash
# Check if ports are available (8000, 8501, 11434, 6379)
# Kill processes using those ports or change in docker-compose.yml

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

### Ollama connection errors

```bash
# Wait longer - Ollama model download takes time
# Check logs
docker-compose logs ollama

# Verify model is pulled
curl http://localhost:11434/api/tags
```

### API returns "Service Unavailable"

```bash
# Ensure all services are healthy
docker-compose ps

# Check individual service health
curl http://localhost:8000/health
curl http://localhost:6379 (should ping)
```

### Out of memory

- Reduce LLM model size in `.env`: Use `qwen2.5-7b` instead of `llama3.1`
- Close other applications
- Increase Docker memory allocation

## 🛑 Stopping Services

**Press Ctrl+C** in terminal, then:

```bash
docker-compose down
```

To remove all data:
```bash
docker-compose down -v
```

## 📚 Next Steps

- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Check [API.md](API.md) for API endpoints reference
- Read [README.md](README.md) for full documentation

## 💡 Tips

- First query might be slow (LLM warm-up)
- Vector store persists between restarts
- Logs available at `./data/logs/cv-reader.log`
- API supports batch uploads - try uploading 5+ CVs
- Use "Reset Database" only in development

---

**Need help?** Check the logs:
```bash
docker-compose logs -f fastapi  # FastAPI logs
docker-compose logs -f ollama   # Ollama logs
```

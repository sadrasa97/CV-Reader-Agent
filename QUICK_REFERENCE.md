# ⚡ Quick Reference - Multi-LLM Provider

## 🚀 30-Second Setup

### Option 1: Use Default (Ollama)
```bash
# Already configured!
# Just start:
docker-compose up
```

### Option 2: Switch to OpenAI
```bash
# 1. Get key: https://platform.openai.com/api-keys
# 2. Edit .env:
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-key

# 3. Install:
pip install langchain-openai

# 4. Restart:
docker-compose restart fastapi
```

### Option 3: Switch to Groq
```bash
# 1. Get key: https://console.groq.com
# 2. Edit .env:
export LLM_PROVIDER=groq
export GROQ_API_KEY=your-key

# 3. Install:
pip install langchain-groq

# 4. Keep Ollama running (for embeddings):
ollama serve  # In another terminal

# 5. Restart:
docker-compose restart fastapi
```

---

## 📋 .env Configuration Templates

### Ollama (Default - Local)
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_EMBED_MODEL=nomic-embed-text
EMBEDDING_PROVIDER=ollama
```

### OpenAI (Cloud - Premium)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4
OPENAI_EMBED_MODEL=text-embedding-3-small
EMBEDDING_PROVIDER=openai
```

### Groq (Cloud - Fast)
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your-key
GROQ_MODEL=mixtral-8x7b-32768
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### Local (Private - GPU)
```env
LLM_PROVIDER=local
LOCAL_MODEL_PATH=meta-llama/Llama-2-7b-hf
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

---

## ✅ Verification Commands

```bash
# Test health check
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Best candidate?"}'

# Check logs
tail -f ./data/logs/cv-reader.log

# Check which provider is active
grep "Initializing LLM client" ./data/logs/cv-reader.log
```

---

## 📊 Provider Comparison (Quick)

| | Ollama | OpenAI | Groq | Local |
|---|--------|--------|------|-------|
| **Cost** | Free | $$$ | Free | Free |
| **Speed** | Medium | Fast | ⚡ | Slow |
| **Quality** | Good | Best | Good | Medium |
| **Setup** | Medium | Easy | Easy | Hard |
| **Privacy** | ✅ | ❌ | ❌ | ✅ |
| **Offline** | ✅ | ❌ | ❌ | ✅ |

---

## 🆘 Common Issues & Fixes

### "Connection refused"
```bash
# Ollama not running?
ollama serve

# Other service issue?
docker-compose down && docker-compose up
```

### "Invalid API key"
```bash
# Check key is set
echo $OPENAI_API_KEY

# Regenerate at:
# https://platform.openai.com/api-keys (OpenAI)
# https://console.groq.com (Groq)
```

### "Embedding provider not found"
```bash
# Groq doesn't provide embeddings - keep Ollama running!
ollama serve  # In terminal 1
docker-compose up  # In terminal 2
```

### "Model not found"
```bash
# Download the model
ollama pull llama3.1  # For Ollama

# Or update .env to use available model
OLLAMA_MODEL=mistral  # Smaller alternative
```

---

## 📝 Environment Variable Reference

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| LLM_PROVIDER | ✅ | ollama | ollama, openai, groq, local |
| OPENAI_API_KEY | ⚠️ | sk-... | Only for OpenAI |
| OPENAI_MODEL | ❌ | gpt-4 | Default: gpt-4 |
| GROQ_API_KEY | ⚠️ | gsk_... | Only for Groq |
| GROQ_MODEL | ❌ | mixtral... | Default: mixtral-8x7b-32768 |
| LOCAL_MODEL_PATH | ⚠️ | meta-llama/... | Only for Local |
| EMBEDDING_PROVIDER | ✅ | ollama | ollama or openai |
| OLLAMA_BASE_URL | ✅ | http://... | Ollama server URL |
| OLLAMA_MODEL | ✅ | llama3.1 | Ollama model name |

---

## 🔄 Switching Providers in Production

```bash
# 1. No downtime required!
# 2. Update .env (or env vars)
# 3. Restart only fastapi service:
docker-compose restart fastapi

# 4. Streamlit will reconnect automatically
# 5. Existing data persists (ChromaDB)
```

---

## 📚 Full Documentation

For detailed information, see:

- **Overview**: MULTI_LLM_UPDATE.md
- **Setup Steps**: PROVIDER_SETUP_GUIDE.md
- **Provider Details**: LLM_PROVIDERS.md
- **Validation**: VALIDATION_REPORT.md
- **API Reference**: API.md

---

## 🎯 Recommended Setups

### Development
```env
LLM_PROVIDER=groq       # Free tier
EMBEDDING_PROVIDER=ollama
```

### Testing
```env
LLM_PROVIDER=ollama     # Private
EMBEDDING_PROVIDER=ollama
```

### Production
```env
LLM_PROVIDER=openai     # Best quality
EMBEDDING_PROVIDER=openai
OPENAI_MODEL=gpt-4
```

### Cost-Conscious
```env
LLM_PROVIDER=groq       # Free
EMBEDDING_PROVIDER=ollama
```

---

## 🚦 Health Check Response

### Healthy Response
```json
{
  "status": "running",
  "version": "1.0.0",
  "services": {
    "llm": "ok",
    "redis": "ok",
    "vector_db": "ok"
  }
}
```

### With Issues
```json
{
  "status": "running",
  "services": {
    "llm": "error",        // Check API key or service
    "redis": "offline",    // Start Redis
    "vector_db": "ok"      // ChromaDB working
  }
}
```

---

## 📊 Cost Estimation

**Monthly (1000 CVs + 5000 queries):**

| Provider | Cost |
|----------|------|
| Ollama | $0 |
| Groq (free tier) | $0 |
| Local | $0 |
| OpenAI gpt-3.5-turbo | $2-3 |
| OpenAI gpt-4 | $45-60 |

---

## ⚙️ Performance Tips

```bash
# For speed: Use Groq
LLM_PROVIDER=groq

# For quality: Use OpenAI
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4

# For cost: Use Groq or Ollama
LLM_PROVIDER=groq

# For privacy: Use Ollama or Local
LLM_PROVIDER=ollama
```

---

## 🔐 API Key Storage

```bash
# DO:
# 1. Store in .env (git-ignored)
# 2. Use environment variables
# 3. Rotate periodically

# DON'T:
# 1. Commit to git
# 2. Share publicly
# 3. Log to console
```

---

## 📞 Quick Links

| Resource | URL |
|----------|-----|
| Ollama | https://ollama.com |
| OpenAI API | https://platform.openai.com |
| Groq Console | https://console.groq.com |
| HuggingFace | https://huggingface.co |

---

**Everything working?** → Upload CVs and start querying! 🎉

**Need help?** → See full documentation files

**Want to switch?** → Update .env and restart 🔄

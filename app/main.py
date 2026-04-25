"""
FastAPI application - CV Reader Agent backend
"""
import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.config import settings
from app.logger import logger
from app.schemas import (
    UploadResponse, TaskResponse, TaskStatus, QueryRequest, QueryResponse,
    HealthResponse, ComparisonRequest
)
from app.vector_store import get_vector_store
from app.cv_processor import process_cv
from app.tasks import process_cv_async
from app.celery_app import celery_app
from app.agent import get_hr_agent

# Create upload directory
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.vector_db_path, exist_ok=True)

# Task storage (in-memory, will be replaced with Celery task tracking)
task_store = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting CV Reader Agent API")
    yield
    logger.info("Shutting down CV Reader Agent API")


# Initialize FastAPI app
app = FastAPI(
    title="CV Reader Agent API",
    description="Production-ready CV analysis pipeline with LangChain agent & function calling",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check application and service health"""
    services = {}
    
    # Check LLM Provider
    try:
        from app.config import LLMProvider, settings
        if settings.llm_provider == LLMProvider.OLLAMA:
            import requests
            resp = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
            services["llm"] = "ok" if resp.status_code == 200 else "error"
        elif settings.llm_provider == LLMProvider.OPENAI:
            services["llm"] = "ok" if settings.openai_api_key else "error"
        elif settings.llm_provider == LLMProvider.GROQ:
            services["llm"] = "ok" if settings.groq_api_key else "error"
        elif settings.llm_provider == LLMProvider.LOCAL:
            services["llm"] = "ok" if settings.local_model_path else "error"
    except Exception as e:
        logger.warning(f"LLM health check failed: {str(e)}")
        services["llm"] = "offline"
    
    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        services["redis"] = "ok"
    except Exception as e:
        logger.warning(f"Redis health check failed: {str(e)}")
        services["redis"] = "offline"
    
    # Check Vector DB
    try:
        vs = get_vector_store()
        candidates = vs.get_all_candidates()
        services["vector_db"] = "ok"
    except Exception as e:
        logger.warning(f"Vector DB health check failed: {str(e)}")
        services["vector_db"] = "error"
    
    return HealthResponse(
        status="running",
        version="1.0.0",
        services=services
    )


# ============================================================================
# CV Upload Endpoints
# ============================================================================

@app.post("/upload", response_model=UploadResponse)
async def upload_cv(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Upload a CV file (PDF or DOCX) for processing
    
    The file is processed asynchronously and added to the vector store.
    Returns a task_id that can be used to check processing status.
    
    Args:
        file: CV file (PDF or DOCX)
    
    Returns:
        UploadResponse with candidate_id and task_id
    """
    try:
        # Validate file type
        if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            if not file.filename.lower().endswith(('.pdf', '.docx')):
                raise HTTPException(400, "Only PDF and DOCX files are supported")
        
        # Generate candidate ID
        candidate_id = uuid.uuid4().hex[:8]
        
        # Save uploaded file
        filepath = os.path.join(settings.upload_dir, f"{candidate_id}_{file.filename}")
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"File uploaded: {filepath} (candidate_id: {candidate_id})")
        
        # Trigger async processing
        task = process_cv_async.delay(filepath, candidate_id)
        task_id = task.id
        
        # Store task info
        task_store[task_id] = {
            "candidate_id": candidate_id,
            "filename": file.filename,
            "status": TaskStatus.PENDING
        }
        
        logger.info(f"Started async task {task_id} for candidate {candidate_id}")
        
        return UploadResponse(
            status="queued",
            candidate_id=candidate_id,
            task_id=task_id,
            filename=file.filename,
            message=f"CV processing started. Use task_id {task_id} to check status."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading CV: {str(e)}")
        raise HTTPException(500, f"Error uploading CV: {str(e)}")


@app.get("/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    Get the status of an async CV processing task
    
    Args:
        task_id: Task ID returned from /upload
    
    Returns:
        TaskResponse with current status and progress
    """
    try:
        # Get task result from Celery
        task_result = celery_app.AsyncResult(task_id)
        
        status_map = {
            'PENDING': TaskStatus.PENDING,
            'STARTED': TaskStatus.PROCESSING,
            'PROGRESS': TaskStatus.PROCESSING,
            'SUCCESS': TaskStatus.SUCCESS,
            'FAILURE': TaskStatus.FAILED,
        }
        
        status = status_map.get(task_result.state, TaskStatus.PENDING)
        
        # Extract progress and metadata
        progress = 0
        metadata = None
        error = None
        
        if task_result.state == 'PROGRESS':
            progress = task_result.info.get('progress', 50)
        elif task_result.state == 'SUCCESS':
            progress = 100
            result = task_result.result
            if isinstance(result, dict):
                # Create CVMetadata from result
                metadata = {
                    "candidate_id": result.get("candidate_id"),
                    "years_experience": result.get("metadata", {}).get("years_experience")
                }
        elif task_result.state == 'FAILURE':
            error = str(task_result.info)
        
        return TaskResponse(
            task_id=task_id,
            status=status,
            progress=progress,
            metadata=metadata,
            error=error
        )
    
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(500, f"Error getting task status: {str(e)}")


@app.get("/candidates")
async def list_candidates():
    """
    List all candidates in the vector store
    
    Returns:
        List of candidates with metadata
    """
    try:
        vector_store = get_vector_store()
        candidates = vector_store.get_all_candidates()
        
        return {
            "status": "ok",
            "total_candidates": len(candidates),
            "candidates": candidates
        }
    
    except Exception as e:
        logger.error(f"Error listing candidates: {str(e)}")
        raise HTTPException(500, f"Error listing candidates: {str(e)}")


@app.delete("/candidates/{candidate_id}")
async def delete_candidate(candidate_id: str):
    """
    Delete a candidate and their CV from the vector store
    
    Args:
        candidate_id: Candidate to delete
    
    Returns:
        Confirmation message
    """
    try:
        vector_store = get_vector_store()
        success = vector_store.delete_candidate(candidate_id)
        
        if success:
            return {"status": "ok", "message": f"Candidate {candidate_id} deleted"}
        else:
            raise HTTPException(404, f"Candidate {candidate_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting candidate: {str(e)}")
        raise HTTPException(500, f"Error deleting candidate: {str(e)}")


@app.post("/reset")
async def reset_database():
    """
    Reset the entire vector database (development only)
    
    Returns:
        Confirmation message
    """
    try:
        vector_store = get_vector_store()
        success = vector_store.clear_all()
        
        if success:
            logger.warning("Vector database reset by user")
            return {"status": "ok", "message": "Vector database reset successfully"}
        else:
            raise HTTPException(500, "Failed to reset database")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        raise HTTPException(500, f"Error resetting database: {str(e)}")


# ============================================================================
# Query Endpoints (Phase 3 - to be implemented)
# ============================================================================

@app.post("/query", response_model=QueryResponse)
async def hr_query(req: QueryRequest):
    """
    Query the HR agent with a question about candidates
    
    The agent will automatically select and invoke appropriate tools
    (search_candidate, compare_candidates, etc.) and return structured results.
    
    Args:
        req: QueryRequest with question and optional top_k
    
    Returns:
        QueryResponse with structured agent answer
    """
    try:
        logger.info(f"Query received: {req.question}")
        
        # Get agent and process query
        agent = get_hr_agent()
        response = agent.query(req.question, top_k=req.top_k)
        
        logger.info(f"Query processed: {response.candidates_found} candidates found, tool used: {response.tool_used}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(500, f"Error processing query: {str(e)}")


@app.post("/compare")
async def compare_candidates(req: ComparisonRequest):
    """
    Compare multiple candidates based on criteria
    
    Args:
        req: ComparisonRequest with criteria and top_k
    
    Returns:
        ComparisonResult with ranked candidates
    """
    try:
        logger.info(f"Comparison requested: {req.criteria}")
        
        # Use agent to compare candidates
        agent = get_hr_agent()
        response = agent.query(
            f"Compare candidates for the following criteria: {req.criteria}",
            top_k=req.top_k
        )
        
        return {
            "status": "ok",
            "criteria": req.criteria,
            "candidates_found": response.candidates_found,
            "results": response.structured_results,
            "summary": response.answer
        }
    
    except Exception as e:
        logger.error(f"Error comparing candidates: {str(e)}")
        raise HTTPException(500, f"Error comparing candidates: {str(e)}")


# ============================================================================
# Root endpoint
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "CV Reader Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "upload": "POST /upload",
            "task_status": "GET /task/{task_id}",
            "list_candidates": "GET /candidates",
            "delete_candidate": "DELETE /candidates/{candidate_id}",
            "query": "POST /query",
            "compare": "POST /compare",
            "reset_db": "POST /reset"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )

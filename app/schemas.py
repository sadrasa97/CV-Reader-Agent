"""
Pydantic schemas for CV Reader Agent API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class CVMetadata(BaseModel):
    """Structured metadata extracted from a CV"""
    candidate_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    years_experience: Optional[int] = None
    skills: List[str] = Field(default_factory=list)
    current_role: Optional[str] = None
    education: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "abc123",
                "name": "John Doe",
                "email": "john@example.com",
                "years_experience": 5,
                "skills": ["Python", "AWS", "FastAPI"],
                "current_role": "Senior Backend Engineer"
            }
        }


class CandidateMatch(BaseModel):
    """A candidate match result from semantic search"""
    candidate_id: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    matched_criteria: List[str] = Field(default_factory=list)
    evidence: str
    metadata: CVMetadata
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "abc123",
                "relevance_score": 0.92,
                "matched_criteria": ["Python", "AWS", "5+ years"],
                "evidence": "Extensive Python experience with AWS deployment...",
                "metadata": {"candidate_id": "abc123", "name": "John Doe"}
            }
        }


class ComparisonResult(BaseModel):
    """Result of comparing multiple candidates"""
    criteria: str
    candidates: List[CandidateMatch]
    ranked_candidates: List[str] = Field(description="Candidate IDs ranked by fit")
    summary: str = Field(description="Human-readable comparison summary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "criteria": "Senior Python Backend Engineer",
                "candidates": [],
                "ranked_candidates": ["cand1", "cand2"],
                "summary": "Candidate cand1 is the best fit..."
            }
        }


class QueryResponse(BaseModel):
    """Structured response from HR agent query"""
    query: str
    tool_used: str = Field(description="Which tool was invoked (search_candidate, compare_candidates, etc.)")
    candidates_found: int
    structured_results: List[CandidateMatch] = Field(default_factory=list)
    answer: str = Field(description="Human-readable agent response")
    reasoning: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Best candidates for Senior Python Backend Engineer",
                "tool_used": "search_candidate",
                "candidates_found": 3,
                "structured_results": [],
                "answer": "Top candidate is John Doe with 5+ years Python experience..."
            }
        }


class UploadResponse(BaseModel):
    """Response from CV upload"""
    status: str
    candidate_id: str
    task_id: Optional[str] = None
    filename: str
    message: Optional[str] = None


class TaskResponse(BaseModel):
    """Status of an async task"""
    task_id: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100)
    metadata: Optional[CVMetadata] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_123",
                "status": "PROCESSING",
                "progress": 50,
                "metadata": None,
                "error": None
            }
        }


class QueryRequest(BaseModel):
    """Request for HR query"""
    question: str = Field(min_length=5, max_length=1000)
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Who is the best fit for Senior Python Backend Engineer with AWS?",
                "top_k": 5
            }
        }


class ComparisonRequest(BaseModel):
    """Request to compare candidates"""
    criteria: str = Field(min_length=5, max_length=1000)
    top_k: Optional[int] = Field(default=3, ge=2, le=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "criteria": "Data Science role with 3+ years ML experience",
                "top_k": 3
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    services: Dict[str, str] = Field(description="Status of dependent services")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "running",
                "version": "1.0.0",
                "services": {
                    "ollama": "ok",
                    "redis": "ok",
                    "vector_db": "ok"
                }
            }
        }

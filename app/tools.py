"""
HR-specific tools for the LangChain agent
"""
from langchain_core.tools import tool
from typing import List
from app.vector_store import get_vector_store
from app.schemas import CandidateMatch, CVMetadata
from app.logger import logger


@tool
def search_candidate(query: str, top_k: int = 5) -> str:
    """
    Search CV database for candidates matching a job requirement or skill.
    
    Use this tool to find candidates with specific skills, experience, or qualifications.
    For example:
    - "Senior Python Backend Engineer with 5+ years AWS experience"
    - "Data Scientist with Machine Learning and TensorFlow skills"
    - "Product Manager with SaaS and B2B experience"
    
    Args:
        query: Job requirement or skill query (e.g., "Senior Python Engineer with AWS")
        top_k: Number of top candidates to return (default: 5, max: 20)
    
    Returns:
        Formatted string with top candidate matches and their relevance scores
    """
    try:
        logger.info(f"Tool: search_candidate - Query: {query}, Top K: {top_k}")
        
        # Ensure top_k is within bounds
        top_k = min(max(1, top_k), 20)
        
        # Perform search
        vector_store = get_vector_store()
        results = vector_store.search(query, k=top_k)
        
        if not results:
            return "No candidates found matching the query."
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            score = result.get("relevance_score", 0)
            name = result.get("name", "Unknown")
            email = result.get("email", "N/A")
            skills = ", ".join(result.get("skills", [])[:5])  # Top 5 skills
            years = result.get("years_experience", "Unknown")
            
            formatted = (
                f"{i}. [{result['candidate_id']}] {name}\n"
                f"   Relevance Score: {score:.2%}\n"
                f"   Email: {email}\n"
                f"   Years Experience: {years}\n"
                f"   Key Skills: {skills}\n"
                f"   Preview: {result['preview']}"
            )
            formatted_results.append(formatted)
        
        return "\n\n".join(formatted_results)
    
    except Exception as e:
        logger.error(f"Error in search_candidate tool: {str(e)}")
        return f"Error during search: {str(e)}"


@tool
def compare_candidates(criteria: str, top_k: int = 3) -> str:
    """
    Compare multiple candidates based on specific criteria.
    
    Use this tool to rank and compare top candidates for a position.
    This provides a structured comparison to help make hiring decisions.
    For example:
    - "Compare candidates for Data Science role based on ML experience"
    - "Rank Senior Backend Engineers by AWS and scalability experience"
    - "Compare Project Managers on stakeholder management and delivery"
    
    Args:
        criteria: Comparison criteria (e.g., "Data Science role with ML focus")
        top_k: Number of candidates to compare (default: 3, min: 2, max: 10)
    
    Returns:
        Structured comparison with rankings and scoring
    """
    try:
        logger.info(f"Tool: compare_candidates - Criteria: {criteria}, Top K: {top_k}")
        
        # Ensure top_k is within bounds
        top_k = min(max(2, top_k), 10)
        
        # Perform search
        vector_store = get_vector_store()
        candidates = vector_store.search(criteria, k=top_k)
        
        if len(candidates) < 2:
            return "Need at least 2 candidates to compare. Please upload more CVs."
        
        # Sort by relevance score (descending)
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )
        
        # Format comparison
        comparison_lines = [f"Comparison Criteria: {criteria}\n"]
        comparison_lines.append(f"Total Candidates: {len(sorted_candidates)}\n")
        comparison_lines.append("=" * 80)
        comparison_lines.append("RANKING:\n")
        
        for rank, candidate in enumerate(sorted_candidates, 1):
            score = candidate.get("relevance_score", 0)
            name = candidate.get("name", "Unknown")
            email = candidate.get("email", "N/A")
            skills = ", ".join(candidate.get("skills", [])[:7])
            years = candidate.get("years_experience", "Unknown")
            
            star_rating = "★" * round(score * 5)
            
            comparison_lines.append(
                f"\n#{rank} - {name} ({candidate['candidate_id']})\n"
                f"    Fit Score: {score:.2%} {star_rating}\n"
                f"    Email: {email}\n"
                f"    Experience: {years} years\n"
                f"    Skills: {skills}"
            )
        
        comparison_lines.append("\n" + "=" * 80)
        return "\n".join(comparison_lines)
    
    except Exception as e:
        logger.error(f"Error in compare_candidates tool: {str(e)}")
        return f"Error during comparison: {str(e)}"


@tool
def get_candidate_details(candidate_id: str) -> str:
    """
    Get detailed information about a specific candidate.
    
    Use this tool to retrieve full details for a candidate you want to focus on.
    
    Args:
        candidate_id: The candidate ID (e.g., "abc12345")
    
    Returns:
        Detailed candidate information
    """
    try:
        logger.info(f"Tool: get_candidate_details - Candidate ID: {candidate_id}")
        
        # Search for the specific candidate
        vector_store = get_vector_store()
        all_candidates = vector_store.get_all_candidates()
        
        candidate = next(
            (c for c in all_candidates if c["candidate_id"] == candidate_id),
            None
        )
        
        if not candidate:
            return f"Candidate {candidate_id} not found."
        
        # Format detailed info
        details = [
            f"Candidate Details: {candidate_id}\n",
            f"Name: {candidate.get('name', 'Unknown')}",
            f"Email: {candidate.get('email', 'N/A')}",
            f"Years of Experience: {candidate.get('years_experience', 'Unknown')}",
            f"Skills: {', '.join(candidate.get('skills', []))}",
        ]
        
        return "\n".join(details)
    
    except Exception as e:
        logger.error(f"Error in get_candidate_details tool: {str(e)}")
        return f"Error retrieving candidate details: {str(e)}"


@tool
def list_all_candidates() -> str:
    """
    List all candidates currently in the database.
    
    Use this to get an overview of all available candidates.
    
    Returns:
        List of all candidates with basic info
    """
    try:
        logger.info("Tool: list_all_candidates")
        
        vector_store = get_vector_store()
        candidates = vector_store.get_all_candidates()
        
        if not candidates:
            return "No candidates found in the database."
        
        # Format list
        lines = [f"Total Candidates: {len(candidates)}\n"]
        lines.append("=" * 80)
        
        for i, candidate in enumerate(candidates, 1):
            lines.append(
                f"{i}. [{candidate['candidate_id']}] {candidate.get('name', 'Unknown')} - "
                f"{candidate.get('years_experience', 0)} years, "
                f"Skills: {', '.join(candidate.get('skills', [])[:3])}"
            )
        
        return "\n".join(lines)
    
    except Exception as e:
        logger.error(f"Error in list_all_candidates tool: {str(e)}")
        return f"Error listing candidates: {str(e)}"


# Tool registry
TOOLS_LIST = [
    search_candidate,
    compare_candidates,
    get_candidate_details,
    list_all_candidates
]

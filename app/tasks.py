"""
Async tasks for CV processing using Celery
"""
from app.celery_app import celery_app
from app.cv_processor import process_cv
from app.vector_store import get_vector_store
from app.logger import logger
import os


@celery_app.task(bind=True)
def process_cv_async(self, filepath: str, candidate_id: str) -> dict:
    """
    Async task to process CV and add to vector store
    
    Args:
        filepath: Path to uploaded CV file
        candidate_id: Unique candidate identifier
    
    Returns:
        Dictionary with processing results
    """
    try:
        logger.info(f"Starting async CV processing for {candidate_id}")
        
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Extracting text...'})
        
        # Process CV
        text, metadata, chunks = process_cv(filepath)
        
        # Update state
        self.update_state(state='PROGRESS', meta={'status': 'Adding to vector store...'})
        
        # Add to vector store
        vector_store = get_vector_store()
        vector_store.add_cv(candidate_id, text, chunks, metadata)
        
        # Update state
        self.update_state(state='PROGRESS', meta={'status': 'Finalizing...'})
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
            logger.info(f"Cleaned up file: {filepath}")
        except Exception as e:
            logger.warning(f"Could not delete file {filepath}: {str(e)}")
        
        logger.info(f"CV processing complete for {candidate_id}")
        
        return {
            "status": "success",
            "candidate_id": candidate_id,
            "metadata": metadata,
            "chunks_count": len(chunks),
            "text_length": len(text)
        }
    
    except Exception as e:
        logger.error(f"Error in CV processing task: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@celery_app.task(bind=True)
def compare_candidates_async(self, criteria: str, top_k: int = 3) -> dict:
    """
    Async task to compare candidates based on criteria
    
    Args:
        criteria: Comparison criteria
        top_k: Number of top candidates to compare
    
    Returns:
        Comparison results
    """
    try:
        logger.info(f"Starting async comparison for: {criteria}")
        
        self.update_state(state='PROGRESS', meta={'status': 'Searching candidates...'})
        
        # Search vector store
        vector_store = get_vector_store()
        candidates = vector_store.search(criteria, k=top_k)
        
        self.update_state(state='PROGRESS', meta={'status': 'Preparing comparison...'})
        
        logger.info(f"Comparison complete: {len(candidates)} candidates found")
        
        return {
            "status": "success",
            "criteria": criteria,
            "candidates_count": len(candidates),
            "candidates": candidates
        }
    
    except Exception as e:
        logger.error(f"Error in comparison task: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

"""
ChromaDB vector store wrapper for semantic search
"""
import os
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.config import settings
from app.logger import logger


class VectorStore:
    """Wrapper around ChromaDB for candidate CV storage and retrieval"""
    
    def __init__(self):
        """Initialize vector store with embeddings"""
        self.db_path = settings.vector_db_path
        
        # Ensure directory exists
        os.makedirs(self.db_path, exist_ok=True)
        
        logger.info(f"Initializing VectorStore at {self.db_path}")
        
        # Get embeddings client (can be Ollama or OpenAI based on config)
        from app.llm import get_embedding_client
        self.embeddings = get_embedding_client()
        
        # Initialize Chroma DB
        self.db = Chroma(
            persist_directory=self.db_path,
            embedding_function=self.embeddings,
            collection_name="candidates"
        )
    
    def add_cv(
        self,
        candidate_id: str,
        text: str,
        chunks: List[str],
        metadata: dict
    ) -> None:
        """
        Add CV chunks to vector store with metadata
        
        Args:
            candidate_id: Unique candidate identifier
            text: Full CV text
            chunks: List of text chunks
            metadata: Extracted metadata (name, email, skills, etc.)
        """
        try:
            logger.info(f"Adding CV for candidate {candidate_id} with {len(chunks)} chunks")
            
            # Create documents from chunks
            documents = []
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "candidate_id": candidate_id,
                        "chunk_index": i,
                        "name": metadata.get("name", ""),
                        "email": metadata.get("email", ""),
                        "skills": ",".join(metadata.get("skills", [])),
                        "years_experience": metadata.get("years_experience", 0),
                        "full_text": text[:500]  # Store first 500 chars for reference
                    }
                )
                documents.append(doc)
            
            # Add to vector store
            self.db.add_documents(documents)
            logger.info(f"Successfully added CV for candidate {candidate_id}")
        
        except Exception as e:
            logger.error(f"Error adding CV to vector store: {str(e)}")
            raise
    
    def search(
        self,
        query: str,
        k: int = 5,
        filters: Optional[dict] = None
    ) -> List[dict]:
        """
        Semantic search for candidates matching query
        
        Args:
            query: Search query (e.g., "Senior Python Backend Engineer")
            k: Number of results to return
            filters: Optional metadata filters
        
        Returns:
            List of search results with metadata
        """
        try:
            logger.info(f"Searching for: {query} (top {k})")
            
            # Perform similarity search
            results = self.db.similarity_search_with_score(query, k=k * 2)  # Get more for deduplication
            
            # Deduplicate by candidate_id and format results
            seen_candidates = set()
            formatted_results = []
            
            for doc, score in results:
                candidate_id = doc.metadata.get("candidate_id")
                
                # Skip if already added (multiple chunks from same CV)
                if candidate_id in seen_candidates:
                    continue
                
                seen_candidates.add(candidate_id)
                
                formatted_results.append({
                    "candidate_id": candidate_id,
                    "relevance_score": 1 - (score / 2),  # Convert distance to relevance (0-1)
                    "name": doc.metadata.get("name", "Unknown"),
                    "email": doc.metadata.get("email", ""),
                    "skills": doc.metadata.get("skills", "").split(",") if doc.metadata.get("skills") else [],
                    "years_experience": doc.metadata.get("years_experience", 0),
                    "preview": doc.page_content[:300] + "..."
                })
                
                if len(formatted_results) >= k:
                    break
            
            logger.info(f"Found {len(formatted_results)} unique candidates")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise
    
    def get_all_candidates(self) -> List[dict]:
        """
        Get all candidates in the vector store
        
        Returns:
            List of unique candidates with their metadata
        """
        try:
            logger.info("Retrieving all candidates")
            
            # Get all documents
            all_docs = self.db.get()
            
            # Deduplicate by candidate_id
            candidates_dict = {}
            
            for doc_id, metadata in zip(all_docs["ids"], all_docs["metadatas"]):
                candidate_id = metadata.get("candidate_id")
                
                if candidate_id not in candidates_dict:
                    candidates_dict[candidate_id] = {
                        "candidate_id": candidate_id,
                        "name": metadata.get("name", "Unknown"),
                        "email": metadata.get("email", ""),
                        "skills": metadata.get("skills", "").split(",") if metadata.get("skills") else [],
                        "years_experience": metadata.get("years_experience", 0),
                    }
            
            candidates = list(candidates_dict.values())
            logger.info(f"Retrieved {len(candidates)} unique candidates")
            return candidates
        
        except Exception as e:
            logger.error(f"Error retrieving candidates: {str(e)}")
            return []
    
    def delete_candidate(self, candidate_id: str) -> bool:
        """
        Delete all documents for a specific candidate
        
        Args:
            candidate_id: Candidate to delete
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting candidate {candidate_id}")
            
            # Get all documents for this candidate
            results = self.db.get(where={"candidate_id": candidate_id})
            
            if results["ids"]:
                self.db.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} documents for candidate {candidate_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting candidate: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """
        Clear all data from vector store (use with caution)
        
        Returns:
            True if successful
        """
        try:
            logger.warning("Clearing entire vector store")
            
            # Delete and recreate database
            import shutil
            if os.path.exists(self.db_path):
                shutil.rmtree(self.db_path)
            
            os.makedirs(self.db_path, exist_ok=True)
            
            # Reinitialize
            self.db = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embeddings,
                collection_name="candidates"
            )
            
            logger.info("Vector store cleared successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            return False


# Global instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get or create global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

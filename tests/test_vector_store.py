"""
Unit tests for vector store module
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from app.vector_store import VectorStore, get_vector_store


@pytest.fixture
def temp_db_path(tmp_path):
    """Create temporary database path"""
    return str(tmp_path / "test_vector_db")


class TestVectorStore:
    """Tests for VectorStore class"""
    
    @pytest.fixture
    def vector_store(self, temp_db_path, monkeypatch):
        """Create mock vector store"""
        # Mock the Ollama embeddings and ChromaDB
        with patch("app.vector_store.OllamaEmbeddings"), \
             patch("app.vector_store.Chroma"):
            monkeypatch.setenv("VECTOR_DB_PATH", temp_db_path)
            store = VectorStore()
            # Mock the internal db object
            store.db = MagicMock()
            return store
    
    def test_vector_store_initialization(self, vector_store):
        """Test VectorStore initializes correctly"""
        assert vector_store.embed_model == "nomic-embed-text"
        assert vector_store.db is not None
    
    def test_add_cv_creates_documents(self, vector_store):
        """Test that add_cv creates documents"""
        vector_store.add_cv(
            candidate_id="test_123",
            text="Full CV text",
            chunks=["Chunk 1", "Chunk 2"],
            metadata={
                "name": "John Doe",
                "email": "john@example.com",
                "skills": ["Python", "AWS"],
                "years_experience": 5
            }
        )
        
        # Verify that add_documents was called
        assert vector_store.db.add_documents.called
        
        # Check that 2 documents were created (2 chunks)
        call_args = vector_store.db.add_documents.call_args
        documents = call_args[0][0]
        assert len(documents) == 2
    
    def test_search_returns_formatted_results(self, vector_store):
        """Test that search returns properly formatted results"""
        # Mock the similarity search response
        mock_doc = Mock()
        mock_doc.metadata = {
            "candidate_id": "test_123",
            "name": "John Doe",
            "email": "john@example.com",
            "skills": "Python,AWS",
            "years_experience": 5
        }
        mock_doc.page_content = "Sample CV content"
        
        vector_store.db.similarity_search_with_score.return_value = [
            (mock_doc, 0.1)  # Distance of 0.1 = high relevance
        ]
        
        results = vector_store.search("Python engineer", k=5)
        
        assert len(results) == 1
        assert results[0]["candidate_id"] == "test_123"
        assert results[0]["name"] == "John Doe"
        assert "Python" in results[0]["skills"]
    
    def test_search_deduplicates_candidates(self, vector_store):
        """Test that search deduplicates by candidate_id"""
        # Create 2 documents with same candidate_id
        mock_doc1 = Mock()
        mock_doc1.metadata = {
            "candidate_id": "test_123",
            "name": "John Doe",
            "email": "john@example.com",
            "skills": "Python",
            "years_experience": 5
        }
        mock_doc1.page_content = "Part 1"
        
        mock_doc2 = Mock()
        mock_doc2.metadata = {
            "candidate_id": "test_123",
            "name": "John Doe",
            "email": "john@example.com",
            "skills": "Python",
            "years_experience": 5
        }
        mock_doc2.page_content = "Part 2"
        
        vector_store.db.similarity_search_with_score.return_value = [
            (mock_doc1, 0.1),
            (mock_doc2, 0.15)
        ]
        
        results = vector_store.search("Python", k=5)
        
        # Should return only 1 candidate (deduplicated)
        assert len(results) == 1
    
    def test_get_all_candidates(self, vector_store):
        """Test retrieving all candidates"""
        vector_store.db.get.return_value = {
            "ids": ["doc1", "doc2"],
            "metadatas": [
                {
                    "candidate_id": "cand1",
                    "name": "John",
                    "email": "john@example.com",
                    "skills": "Python,AWS",
                    "years_experience": 5
                },
                {
                    "candidate_id": "cand2",
                    "name": "Jane",
                    "email": "jane@example.com",
                    "skills": "Java,Kubernetes",
                    "years_experience": 3
                }
            ]
        }
        
        results = vector_store.get_all_candidates()
        
        assert len(results) == 2
        assert results[0]["candidate_id"] == "cand1"
        assert results[1]["candidate_id"] == "cand2"
    
    def test_delete_candidate(self, vector_store):
        """Test deleting a candidate"""
        vector_store.db.get.return_value = {
            "ids": ["doc1", "doc2"]
        }
        
        success = vector_store.delete_candidate("test_123")
        
        assert success is True
        assert vector_store.db.delete.called
    
    def test_clear_all_deletes_database(self, vector_store, temp_db_path):
        """Test clearing the entire database"""
        # Create a dummy directory
        os.makedirs(temp_db_path, exist_ok=True)
        
        with patch("app.vector_store.shutil.rmtree"), \
             patch("app.vector_store.os.makedirs"), \
             patch("app.vector_store.Chroma"):
            success = vector_store.clear_all()
            assert success is True


class TestGetVectorStore:
    """Tests for global vector store singleton"""
    
    def test_get_vector_store_returns_instance(self):
        """Test that get_vector_store returns a VectorStore"""
        with patch("app.vector_store.VectorStore"):
            store = get_vector_store()
            assert store is not None
    
    def test_get_vector_store_singleton(self):
        """Test that get_vector_store returns same instance"""
        with patch("app.vector_store.VectorStore"):
            store1 = get_vector_store()
            store2 = get_vector_store()
            # Should be same object
            assert store1 is store2


class TestVectorStoreIntegration:
    """Integration tests for vector store"""
    
    def test_add_and_search_workflow(self, temp_db_path):
        """Test add → search workflow"""
        # This is an integration test that would use real embeddings
        # Skipped if Ollama not available
        pytest.skip("Integration test - requires Ollama running")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

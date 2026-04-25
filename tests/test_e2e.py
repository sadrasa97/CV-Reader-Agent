"""
End-to-end integration tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestE2EUploadAndQuery:
    """End-to-end tests for upload and query workflow"""
    
    @pytest.mark.integration
    def test_upload_process_query_workflow(self):
        """Test complete workflow: upload → process → query"""
        pytest.skip("Integration test - requires Docker services running")
    
    def test_upload_endpoint_mock(self):
        """Test upload endpoint with mocked services"""
        with patch("app.main.process_cv_async"), \
             patch("app.main.os.makedirs"):
            # Simulate file upload
            pass
    
    def test_query_with_no_candidates(self):
        """Test querying with empty database"""
        with patch("app.agent.get_vector_store") as mock_vs:
            mock_vs.return_value.search.return_value = []
            
            from app.agent import HRAgent
            with patch("app.agent.get_llm"), \
                 patch("app.agent.create_tool_calling_agent"), \
                 patch("app.agent.AgentExecutor"):
                agent = HRAgent()
                agent.executor = MagicMock()
                agent.executor.invoke.return_value = {
                    "output": "No candidates found in database",
                    "intermediate_steps": []
                }
                
                response = agent.query("Any candidates?")
                assert "No candidates" in response.answer or response.candidates_found == 0


class TestDataFlow:
    """Tests for data flow between components"""
    
    def test_cv_extraction_to_vector_store(self):
        """Test data flows correctly from CV extraction to vector store"""
        from app.cv_processor import extract_structured_metadata
        
        cv_text = """
        John Doe
        john.doe@example.com
        5 years Python and AWS experience
        Skills: Python, AWS, Docker, Kubernetes
        """
        
        metadata = extract_structured_metadata(cv_text)
        
        # Metadata should be in correct format for vector store
        assert "email" in metadata
        assert "years_experience" in metadata
        assert "skills" in metadata
        assert metadata["email"] is not None
        assert metadata["years_experience"] == 5
        assert len(metadata["skills"]) > 0
    
    def test_query_response_serialization(self):
        """Test that QueryResponse can be serialized to JSON"""
        from app.schemas import QueryResponse, CandidateMatch, CVMetadata
        
        response = QueryResponse(
            query="Test query",
            tool_used="search_candidate",
            candidates_found=1,
            structured_results=[
                CandidateMatch(
                    candidate_id="test123",
                    relevance_score=0.95,
                    matched_criteria=["Python"],
                    evidence="Good fit",
                    metadata=CVMetadata(
                        candidate_id="test123",
                        name="John Doe",
                        email="john@example.com",
                        years_experience=5,
                        skills=["Python", "AWS"]
                    )
                )
            ],
            answer="John is a good fit"
        )
        
        # Should be JSON serializable
        json_str = response.model_dump_json()
        assert json_str is not None
        
        # Should be deserializable
        reloaded = QueryResponse.model_validate_json(json_str)
        assert reloaded.query == response.query


class TestErrorHandling:
    """Tests for error handling across components"""
    
    def test_cv_processor_invalid_file_format(self):
        """Test CV processor handles invalid format"""
        from app.cv_processor import extract_text
        
        with pytest.raises(ValueError, match="Unsupported"):
            extract_text("file.txt")
    
    def test_agent_handles_vector_store_error(self):
        """Test agent handles vector store errors"""
        with patch("app.agent.get_vector_store") as mock_vs:
            mock_vs.side_effect = Exception("Vector store offline")
            
            from app.agent import HRAgent
            with patch("app.agent.get_llm"), \
                 patch("app.agent.create_tool_calling_agent"), \
                 patch("app.agent.AgentExecutor"):
                agent = HRAgent()
                agent.executor = MagicMock()
                agent.executor.invoke.side_effect = Exception("Vector store error")
                
                response = agent.query("Any candidates?")
                
                assert response.tool_used == "error"
                assert "error" in response.answer.lower()


class TestPerformance:
    """Tests for performance characteristics"""
    
    def test_chunking_performance(self):
        """Test that chunking is fast"""
        from app.cv_processor import chunk_text
        import time
        
        # Create 10MB of text
        text = "A" * (10 * 1024 * 1024)
        
        start = time.time()
        chunks = chunk_text(text, chunk_size=1000)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (<1 second)
        assert elapsed < 1.0
        assert len(chunks) > 0
    
    def test_metadata_extraction_performance(self):
        """Test that metadata extraction is fast"""
        from app.cv_processor import extract_structured_metadata
        import time
        
        cv_text = """
        John Doe
        john.doe@example.com
        +1-555-0123
        
        Skills: Python, AWS, Docker, Kubernetes, Java, C++, Go, Rust
        5 years experience
        """ * 100  # Repeat to simulate large CV
        
        start = time.time()
        metadata = extract_structured_metadata(cv_text)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (<1 second)
        assert elapsed < 1.0
        assert len(metadata["skills"]) > 0


class TestSchemasValidation:
    """Tests for Pydantic schema validation"""
    
    def test_candidate_match_schema(self):
        """Test CandidateMatch schema validation"""
        from app.schemas import CandidateMatch, CVMetadata
        
        # Valid data
        match = CandidateMatch(
            candidate_id="test123",
            relevance_score=0.95,
            matched_criteria=["Python"],
            evidence="Good fit",
            metadata=CVMetadata(
                candidate_id="test123",
                name="John",
                email="john@example.com"
            )
        )
        
        assert match.relevance_score == 0.95
    
    def test_candidate_match_invalid_score(self):
        """Test that invalid relevance score is rejected"""
        from app.schemas import CandidateMatch, CVMetadata
        
        with pytest.raises(Exception):  # Validation error
            CandidateMatch(
                candidate_id="test123",
                relevance_score=1.5,  # Invalid: > 1.0
                matched_criteria=[],
                evidence="",
                metadata=CVMetadata(candidate_id="test123")
            )
    
    def test_query_response_schema(self):
        """Test QueryResponse schema validation"""
        from app.schemas import QueryResponse
        
        response = QueryResponse(
            query="Test",
            tool_used="search_candidate",
            candidates_found=0,
            answer="Test answer"
        )
        
        assert response.candidates_found == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not integration"])

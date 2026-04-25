"""
Unit tests for LangChain agent module
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agent import HRAgent, get_hr_agent
from app.schemas import QueryResponse


class TestHRAgent:
    """Tests for HRAgent class"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock HR agent"""
        with patch("app.agent.get_llm"), \
             patch("app.agent.create_tool_calling_agent"), \
             patch("app.agent.AgentExecutor"):
            agent = HRAgent()
            agent.executor = MagicMock()
            return agent
    
    def test_agent_initialization(self, mock_agent):
        """Test that agent initializes correctly"""
        assert mock_agent.llm is not None
        assert mock_agent.prompt is not None
        assert mock_agent.executor is not None
    
    def test_query_success(self, mock_agent):
        """Test successful query execution"""
        # Mock executor response
        mock_agent.executor.invoke.return_value = {
            "output": "John Doe [abc12345] is the best fit for Senior Python Engineer.",
            "intermediate_steps": [
                (Mock(tool="search_candidate", tool_input="Senior Python Engineer"), "Found 3 candidates")
            ]
        }
        
        response = mock_agent.query("Best candidate for Python engineer?", top_k=5)
        
        assert isinstance(response, QueryResponse)
        assert response.query == "Best candidate for Python engineer?"
        assert response.tool_used == "search_candidate"
        assert "John Doe" in response.answer or "[abc12345]" in response.answer
    
    def test_query_handles_error(self, mock_agent):
        """Test that query handles errors gracefully"""
        mock_agent.executor.invoke.side_effect = Exception("LLM timeout")
        
        response = mock_agent.query("Some query")
        
        assert isinstance(response, QueryResponse)
        assert response.tool_used == "error"
        assert "error" in response.answer.lower() or "timeout" in response.answer.lower()
    
    def test_query_extracts_candidate_ids(self, mock_agent):
        """Test that query extracts candidate IDs from response"""
        mock_agent.executor.invoke.return_value = {
            "output": "Top candidates: [abc12345] and [def67890]. Both excellent fits.",
            "intermediate_steps": []
        }
        
        with patch("app.agent.get_vector_store") as mock_vs:
            mock_vs.return_value.get_all_candidates.return_value = [
                {
                    "candidate_id": "abc12345",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "years_experience": 5,
                    "skills": ["Python", "AWS"]
                },
                {
                    "candidate_id": "def67890",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "years_experience": 3,
                    "skills": ["Python", "Docker"]
                }
            ]
            
            response = mock_agent.query("Find best candidates")
            
            assert response.candidates_found == 2
            assert len(response.structured_results) == 2
    
    def test_query_with_top_k(self, mock_agent):
        """Test that top_k is passed correctly"""
        mock_agent.executor.invoke.return_value = {
            "output": "Found top 10 candidates",
            "intermediate_steps": []
        }
        
        response = mock_agent.query("Show candidates", top_k=10)
        
        assert mock_agent.executor.invoke.called
        call_args = mock_agent.executor.invoke.call_args[0][0]
        assert "10" in str(call_args)
    
    def test_query_response_structure(self, mock_agent):
        """Test that QueryResponse has all required fields"""
        mock_agent.executor.invoke.return_value = {
            "output": "Response text",
            "intermediate_steps": [
                (Mock(tool="search_candidate", tool_input="query"), "result")
            ]
        }
        
        response = mock_agent.query("Test query")
        
        # Check all required fields exist
        assert hasattr(response, "query")
        assert hasattr(response, "tool_used")
        assert hasattr(response, "candidates_found")
        assert hasattr(response, "structured_results")
        assert hasattr(response, "answer")
        assert hasattr(response, "reasoning")


class TestGetHRAgent:
    """Tests for global HR agent singleton"""
    
    def test_get_hr_agent_returns_instance(self):
        """Test that get_hr_agent returns an HRAgent"""
        with patch("app.agent.HRAgent"):
            agent = get_hr_agent()
            assert agent is not None
    
    def test_get_hr_agent_singleton(self):
        """Test that get_hr_agent returns same instance"""
        with patch("app.agent.HRAgent"):
            agent1 = get_hr_agent()
            agent2 = get_hr_agent()
            assert agent1 is agent2


class TestAgentToolCalling:
    """Tests for agent tool calling behavior"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create agent with mocked tools"""
        with patch("app.agent.get_llm"), \
             patch("app.agent.create_tool_calling_agent"), \
             patch("app.agent.AgentExecutor"):
            agent = HRAgent()
            agent.executor = MagicMock()
            return agent
    
    def test_agent_uses_search_tool(self, mock_agent):
        """Test agent correctly uses search_candidate tool"""
        mock_agent.executor.invoke.return_value = {
            "output": "Found 5 Python developers",
            "intermediate_steps": [
                (Mock(tool="search_candidate", tool_input="Python engineer"), "results")
            ]
        }
        
        response = mock_agent.query("Find Python engineers")
        
        assert response.tool_used == "search_candidate"
    
    def test_agent_uses_compare_tool(self, mock_agent):
        """Test agent correctly uses compare_candidates tool"""
        mock_agent.executor.invoke.return_value = {
            "output": "Comparison results",
            "intermediate_steps": [
                (Mock(tool="compare_candidates", tool_input="compare criteria"), "results")
            ]
        }
        
        response = mock_agent.query("Compare top candidates")
        
        assert response.tool_used == "compare_candidates"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

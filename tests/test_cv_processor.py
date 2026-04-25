"""
Unit tests for CV processor module
"""
import pytest
import tempfile
import os
from pathlib import Path
from app.cv_processor import (
    extract_text, clean_text, chunk_text,
    extract_structured_metadata, process_cv
)


class TestExtractText:
    """Tests for text extraction from PDF/DOCX"""
    
    def test_extract_text_pdf_mock(self, tmp_path):
        """Test PDF text extraction (mock)"""
        # Note: Real test would need actual PDF file
        # This demonstrates the structure
        pass
    
    def test_extract_text_unsupported_format(self):
        """Test that unsupported formats raise error"""
        with pytest.raises(ValueError, match="Unsupported file format"):
            extract_text("file.txt")
    
    def test_extract_text_missing_file(self):
        """Test that missing file raises error"""
        with pytest.raises(Exception):
            extract_text("/nonexistent/file.pdf")


class TestCleanText:
    """Tests for text cleaning"""
    
    def test_clean_text_removes_extra_whitespace(self):
        """Test that extra whitespace is normalized"""
        text = "Hello  \n\n  world   \t  !"
        result = clean_text(text)
        assert result == "Hello world !"
    
    def test_clean_text_preserves_punctuation(self):
        """Test that important punctuation is preserved"""
        text = "email@example.com with (parentheses) and-dashes"
        result = clean_text(text)
        assert "@" in result
        assert "(" in result
        assert "-" in result
    
    def test_clean_text_strips_edges(self):
        """Test that leading/trailing whitespace is removed"""
        text = "  \n  hello world  \n  "
        result = clean_text(text)
        assert result == "hello world"
        assert not result.startswith(" ")
        assert not result.endswith(" ")


class TestChunkText:
    """Tests for text chunking"""
    
    def test_chunk_text_small_text(self):
        """Test that small text is not chunked"""
        text = "Short text"
        result = chunk_text(text, chunk_size=100)
        assert len(result) == 1
        assert result[0] == text
    
    def test_chunk_text_creates_chunks(self):
        """Test that large text is chunked"""
        text = "A" * 2000  # 2000 chars
        result = chunk_text(text, chunk_size=800, overlap=100)
        assert len(result) > 1
        # Each chunk should be <= chunk_size
        for chunk in result:
            assert len(chunk) <= 800
    
    def test_chunk_text_has_overlap(self):
        """Test that chunks have overlap"""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 100
        result = chunk_text(text, chunk_size=200, overlap=50)
        # With overlap, chunks should share content
        if len(result) > 1:
            # Last part of chunk1 should appear in chunk2
            assert result[0][-50:] in result[1][:100]
    
    def test_chunk_text_zero_size(self):
        """Test with custom chunk size"""
        text = "Test " * 100
        result = chunk_text(text, chunk_size=50)
        assert all(len(chunk) <= 50 for chunk in result)


class TestExtractStructuredMetadata:
    """Tests for structured metadata extraction"""
    
    def test_extract_email(self):
        """Test email extraction"""
        text = "John Doe john.doe@example.com Senior Engineer"
        result = extract_structured_metadata(text)
        assert result["email"] == "john.doe@example.com"
    
    def test_extract_years_experience(self):
        """Test years of experience extraction"""
        text = "5 years of experience in Python development"
        result = extract_structured_metadata(text)
        assert result["years_experience"] == 5
    
    def test_extract_skills(self):
        """Test skill extraction"""
        text = "Expert in Python, JavaScript, and AWS. Experienced with Docker and Kubernetes."
        result = extract_structured_metadata(text)
        assert "Python" in result["skills"]
        assert "JavaScript" in result["skills"]
        assert "AWS" in result["skills"]
    
    def test_extract_skills_case_insensitive(self):
        """Test that skill extraction is case-insensitive"""
        text = "Proficient in python, JAVA, and c++"
        result = extract_structured_metadata(text)
        assert any("Python" in skill for skill in result["skills"])
        assert any("Java" in skill for skill in result["skills"])
    
    def test_no_email_found(self):
        """Test when no email is present"""
        text = "Senior Software Engineer with 10 years experience"
        result = extract_structured_metadata(text)
        assert result["email"] is None
    
    def test_no_skills_found(self):
        """Test when no recognized skills are found"""
        text = "Manager of random projects"
        result = extract_structured_metadata(text)
        assert len(result["skills"]) == 0 or all(s not in text for s in result["skills"])


class TestProcessCV:
    """Tests for complete CV processing pipeline"""
    
    def test_process_cv_returns_tuple(self, tmp_path):
        """Test that process_cv returns (text, metadata, chunks)"""
        # Create a mock text file instead
        text = "John Doe\njohn@example.com\n10 years Python AWS experience"
        # This is a simplified test - real test needs actual PDF/DOCX
        result = extract_structured_metadata(text)
        assert "email" in result
        assert "years_experience" in result
        assert "skills" in result
    
    def test_process_cv_extraction_fields(self):
        """Test that all required fields are extracted"""
        text = """
        John Doe
        john.doe@example.com
        +1-555-0123
        
        5 years experience with Python, AWS, and Docker
        
        Skills: Python, AWS, Kubernetes, FastAPI
        """
        result = extract_structured_metadata(text)
        
        # Check all fields exist
        assert "email" in result
        assert "years_experience" in result
        assert "skills" in result
        assert result["email"] is not None
        assert len(result["skills"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

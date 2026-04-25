"""
Pytest configuration and fixtures
"""
import pytest
import os
from unittest.mock import patch


@pytest.fixture(scope="session")
def mock_env():
    """Mock environment variables for testing"""
    env_vars = {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "llama3.1",
        "REDIS_URL": "redis://localhost:6379/0",
        "VECTOR_DB_PATH": "./data/vector_db_test",
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def temp_cv_text():
    """Sample CV text for testing"""
    return """
    JOHN DOE
    john.doe@example.com | +1-555-0123 | LinkedIn: linkedin.com/in/johndoe
    
    PROFESSIONAL SUMMARY
    Senior Software Engineer with 5 years of experience in full-stack development.
    Expert in Python, AWS, and cloud architecture. Strong background in DevOps and containerization.
    
    SKILLS
    - Programming Languages: Python, JavaScript, Java, Go
    - Cloud Platforms: AWS (EC2, S3, Lambda, RDS), Azure
    - DevOps: Docker, Kubernetes, Jenkins, CI/CD
    - Databases: PostgreSQL, MongoDB, Redis
    - Frameworks: FastAPI, Django, React, Node.js
    - Other: Git, Linux, Agile/Scrum
    
    PROFESSIONAL EXPERIENCE
    
    Senior Backend Engineer | Tech Company Inc. | Jan 2020 - Present
    - Led development of microservices architecture using FastAPI and Kubernetes
    - Reduced API response time by 40% through optimization
    - Managed team of 3 junior developers
    - Implemented CI/CD pipeline with Jenkins and Docker
    
    Backend Developer | Startup XYZ | Jun 2018 - Dec 2019
    - Developed REST APIs using Python and FastAPI
    - Deployed applications to AWS using EC2 and RDS
    - Implemented real-time features using WebSockets
    - Reduced database query time by 60% through indexing
    
    EDUCATION
    Bachelor of Science in Computer Science | University Name | 2018
    
    CERTIFICATIONS
    - AWS Certified Solutions Architect - Associate (2021)
    - Docker Certified Associate (2020)
    """


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (slow)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )

"""
CV text extraction and processing
"""
import os
from typing import Tuple
import re
from pypdf import PdfReader
from docx import Document
from app.logger import logger


def extract_text(filepath: str) -> str:
    """
    Extract text from PDF or DOCX files
    
    Args:
        filepath: Path to CV file (PDF or DOCX)
    
    Returns:
        Extracted text content
    
    Raises:
        ValueError: If file format is not supported
    """
    ext = os.path.splitext(filepath)[1].lower()
    
    try:
        if ext == ".pdf":
            logger.info(f"Extracting text from PDF: {filepath}")
            reader = PdfReader(filepath)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            logger.debug(f"Extracted {len(text)} characters from PDF")
            return text
        
        elif ext == ".docx":
            logger.info(f"Extracting text from DOCX: {filepath}")
            doc = Document(filepath)
            text = "\n".join(p.text for p in doc.paragraphs)
            logger.debug(f"Extracted {len(text)} characters from DOCX")
            return text
        
        else:
            raise ValueError(f"Unsupported file format: {ext}. Only PDF and DOCX are supported.")
    
    except Exception as e:
        logger.error(f"Error extracting text from {filepath}: {str(e)}")
        raise


def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Raw text to clean
    
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\-.,@#()/+]', '', text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100
) -> list[str]:
    """
    Split text into overlapping chunks for semantic indexing
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    logger.debug(f"Created {len(chunks)} chunks from {len(text)} chars")
    return chunks


def extract_structured_metadata(text: str) -> dict:
    """
    Extract structured metadata from CV text using regex patterns
    
    Args:
        text: CV text content
    
    Returns:
        Dictionary with extracted metadata (name, email, phone, skills, years_exp)
    """
    metadata = {
        "name": None,
        "email": None,
        "phone": None,
        "years_experience": None,
        "skills": [],
        "education": []
    }
    
    try:
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            metadata["email"] = emails[0]
        
        # Extract phone numbers
        phone_pattern = r'\+?1?\d{9,15}'
        phones = re.findall(phone_pattern, text)
        if phones:
            metadata["phone"] = phones[0]
        
        # Extract years of experience
        exp_pattern = r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:experience|exp|of\s+work)'
        exp_matches = re.findall(exp_pattern, text.lower())
        if exp_matches:
            metadata["years_experience"] = int(exp_matches[0])
        
        # Extract skills (common tech keywords)
        skills_list = [
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "php", "ruby",
            "react", "vue", "angular", "fastapi", "django", "flask", "spring", "node.js",
            "aws", "azure", "gcp", "kubernetes", "docker", "git", "jenkins",
            "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
            "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch",
            "agile", "scrum", "devops", "ci/cd", "rest api", "graphql"
        ]
        
        text_lower = text.lower()
        for skill in skills_list:
            if skill in text_lower:
                metadata["skills"].append(skill.title())
        
        # Remove duplicates and sort
        metadata["skills"] = sorted(list(set(metadata["skills"])))
        
        logger.debug(f"Extracted metadata: {metadata}")
        
    except Exception as e:
        logger.error(f"Error extracting metadata: {str(e)}")
    
    return metadata


def process_cv(filepath: str) -> Tuple[str, dict, list[str]]:
    """
    Complete CV processing pipeline
    
    Args:
        filepath: Path to CV file
    
    Returns:
        Tuple of (cleaned_text, metadata_dict, chunks_list)
    """
    logger.info(f"Starting CV processing: {filepath}")
    
    # Extract text
    text = extract_text(filepath)
    
    # Clean text
    cleaned_text = clean_text(text)
    
    # Extract structured metadata
    metadata = extract_structured_metadata(cleaned_text)
    
    # Create chunks
    chunks = chunk_text(cleaned_text)
    
    logger.info(f"CV processing complete: {len(chunks)} chunks created")
    
    return cleaned_text, metadata, chunks

"""
Parser Module - Phase 1
Handles processing of raw text and PDF inputs into structured format.
"""

import io
import re
from typing import Optional
from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text content from PDF bytes."""
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        
        text_content = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
        
        return "\n\n".join(text_content)
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def clean_text(raw_text: str) -> str:
    """Clean and normalize raw text content."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', raw_text)
    # Remove special characters that might interfere with parsing
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\$\%\(\)\[\]\"\']', '', text)
    # Normalize line breaks
    text = text.replace('. ', '.\n')
    return text.strip()


def parse_earnings_content(content: str, is_pdf: bool = False, pdf_bytes: Optional[bytes] = None) -> dict:
    """
    Parse earnings report content into structured format.
    
    Args:
        content: Raw text content (if not PDF)
        is_pdf: Whether the content is from a PDF
        pdf_bytes: Raw PDF bytes if is_pdf is True
    
    Returns:
        Dictionary containing parsed and structured content
    """
    if is_pdf and pdf_bytes:
        raw_text = extract_text_from_pdf(pdf_bytes)
    else:
        raw_text = content
    
    cleaned_text = clean_text(raw_text)
    
    # Attempt to extract key sections
    sections = {
        "raw_content": raw_text,
        "cleaned_content": cleaned_text,
        "word_count": len(cleaned_text.split()),
        "sections_identified": []
    }
    
    # Common earnings report section patterns
    section_patterns = [
        (r'revenue|sales', 'Revenue/Sales'),
        (r'earnings|profit|income', 'Earnings/Profit'),
        (r'guidance|outlook|forecast', 'Guidance/Outlook'),
        (r'risk|challenges|headwinds', 'Risks/Challenges'),
        (r'growth|expansion|opportunity', 'Growth/Opportunities'),
        (r'debt|liability|borrowing', 'Debt/Liabilities'),
        (r'cash flow|liquidity', 'Cash Flow/Liquidity'),
        (r'margin|profitability', 'Margins'),
    ]
    
    text_lower = cleaned_text.lower()
    for pattern, section_name in section_patterns:
        if re.search(pattern, text_lower):
            sections["sections_identified"].append(section_name)
    
    return sections


def format_for_agents(parsed_content: dict) -> str:
    """
    Format parsed content into a structured prompt for agents.
    
    Args:
        parsed_content: Dictionary from parse_earnings_content
    
    Returns:
        Formatted markdown string for agent consumption
    """
    output = []
    output.append("# Earnings Report Content\n")
    output.append(f"**Word Count:** {parsed_content['word_count']}\n")
    
    if parsed_content['sections_identified']:
        output.append("**Identified Topics:** " + ", ".join(parsed_content['sections_identified']) + "\n")
    
    output.append("\n## Full Content\n")
    output.append("```")
    output.append(parsed_content['cleaned_content'])
    output.append("```")
    
    return "\n".join(output)

"""
Parser Module - Phase 1 (LlamaCloud Integrated)
Handles processing of raw text and PDF inputs into structured format using LlamaCloud.
"""

import io
import os
import re
import tempfile
import asyncio
import requests
from typing import Optional, List
from dotenv import load_dotenv

# Workaround for Pydantic error in llama-cloud: MetadataFilters must be in namespace
try:
    from llama_index.core.vector_stores import MetadataFilters
except ImportError:
    pass

from llama_cloud.client import AsyncLlamaCloud
import md_postprocess

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

# Load environment variables
load_dotenv()

async def pdf_to_markdown(
    *,
    pdf_path: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
    pdf_url: Optional[str] = None,
) -> str:
    """Convert a PDF financial report to a single raw Markdown string using LlamaCloud."""
    # 1. Validate inputs
    inputs = [pdf_path, pdf_bytes, pdf_url]
    if sum(x is not None for x in inputs) != 1:
        raise ValueError("Exactly one of pdf_path, pdf_bytes, or pdf_url must be provided.")

    temp_file = None
    target_path = pdf_path

    try:
        # 2. Resolve input to a local path
        if pdf_url:
            try:
                response = requests.get(pdf_url, timeout=30)
                response.raise_for_status()
                pdf_bytes = response.content
            except Exception as e:
                raise ValueError(f"Failed to download PDF from URL: {e}")

        if pdf_bytes:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.write(pdf_bytes)
            temp_file.close()
            target_path = temp_file.name

        # 3. Parse with AsyncLlamaCloud (fallback to local PDF text extraction)
        api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        if api_key:
            try:
                client = AsyncLlamaCloud(token=api_key)

                # Step A: Upload the file
                print(f"Uploading file: {target_path}...")
                with open(target_path, "rb") as f:
                    file_obj = await client.files.upload_file(upload_file=f)

                # Step B: Parse the file with expansion to get content
                print(f"Parsing file (ID: {file_obj.id})...")
                result = await client.parsing.parse(
                    file_id=file_obj.id,
                    tier="agentic",
                    version="latest",
                    expand=["markdown"]
                )

                # Extract markdown content from expanded result
                md = ""
                pages_list = []
                if hasattr(result, "markdown") and result.markdown and hasattr(result.markdown, "pages"):
                    pages_list = [p.markdown for p in result.markdown.pages if p.markdown]
                    md = "\n\n".join(pages_list)

                if md:
                    # 4. Post-processing
                    cleaned_pages = md_postprocess.remove_repeated_headers_footers(pages_list)
                    md = "\n\n".join(cleaned_pages)
                    md = md_postprocess.dehyphenate(md)
                    md = md_postprocess.fix_hard_wraps(md)
                    md = md_postprocess.wrap_uncertain_tables(md)
                    return md

                print("[WARNING] No markdown content found in expanded results. Falling back to local parser.")
            except Exception as e:
                print(f"[WARNING] LlamaCloud parse failed: {e}. Falling back to local parser.")
        else:
            print("[INFO] LLAMA_CLOUD_API_KEY not set. Falling back to local parser.")

        if PdfReader is None:
            raise ValueError("PyPDF2 is not installed. Install it to enable local PDF parsing.")

        # Local PDF text extraction fallback
        text_pages = []
        with open(target_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text_pages.append(page_text)

        md = "\n\n".join(text_pages)
        md = md_postprocess.dehyphenate(md)
        md = md_postprocess.fix_hard_wraps(md)
        return md

    finally:
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.remove(temp_file.name)
            except:
                pass

def clean_text(raw_text: str) -> str:
    """Clean and normalize raw text content (for non-PDF inputs)."""
    # Use post-processing logic for consistency even for raw text
    text = md_postprocess.dehyphenate(raw_text)
    text = md_postprocess.fix_hard_wraps(text)
    return text.strip()

async def parse_earnings_content(content: str, is_pdf: bool = False, pdf_bytes: Optional[bytes] = None) -> dict:
    """
    Parse earnings report content into structured format (Async version).
    
    Args:
        content: Raw text content (if not PDF)
        is_pdf: Whether the content is from a PDF
        pdf_bytes: Raw PDF bytes if is_pdf is True
    
    Returns:
        Dictionary containing parsed and structured content
    """
    if is_pdf and pdf_bytes:
        raw_text = await pdf_to_markdown(pdf_bytes=pdf_bytes)
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
    output.append("```markdown\n")
    output.append(parsed_content['cleaned_content'])
    output.append("\n```")
    
    return "\n".join(output)

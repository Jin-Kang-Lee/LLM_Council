import re
from collections import Counter

def remove_repeated_headers_footers(pages: list[str]) -> list[str]:
    """
    Split parsed output by pages if possible. Heuristic based on repetition.
    """
    if not pages:
        return []
        
    num_pages = len(pages)
    if num_pages < 3:
        return pages  # Not enough data to confidently detect repetitions

    header_candidates = []
    footer_candidates = []

    for page in pages:
        lines = [line.strip() for line in page.split('\n') if line.strip()]
        # Collect first 5 and last 5 lines
        header_candidates.extend(lines[:5])
        footer_candidates.extend(lines[-5:])

    def get_removable(candidates, threshold=0.3):
        normalized = []
        for c in candidates:
            # Normalize: lowercase, collapse whitespace, strip punctuation, replace numbers
            norm = c.lower()
            norm = re.sub(r'\s+', ' ', norm)
            norm = re.sub(r'[^\w\s]', '', norm)
            norm = re.sub(r'\d+', '<PAGE>', norm)
            normalized.append(norm)
        
        counts = Counter(normalized)
        removable = {norm for norm, count in counts.items() if (count / num_pages) >= threshold}
        return removable

    removable_headers = get_removable(header_candidates)
    removable_footers = get_removable(footer_candidates)

    cleaned_pages = []
    for page in pages:
        lines = page.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                new_lines.append(line)
                continue
                
            norm = stripped.lower()
            norm = re.sub(r'\s+', ' ', norm)
            norm = re.sub(r'[^\w\s]', '', norm)
            norm = re.sub(r'\d+', '<PAGE>', norm)
            
            # Check if it's in top 5 or bottom 5 of the page lines (after stripping empty)
            is_header_pos = i < 10 # heuristic index
            is_footer_pos = i > len(lines) - 10
            
            if (is_header_pos and norm in removable_headers) or (is_footer_pos and norm in removable_footers):
                continue
            
            new_lines.append(line)
        cleaned_pages.append('\n'.join(new_lines))
        
    return cleaned_pages

def fix_hard_wraps(text: str) -> str:
    """
    Join lines into paragraphs if they look like hard-wrapped text.
    """
    lines = text.split('\n')
    result = []
    current_para = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_para:
                result.append(" ".join(current_para))
                current_para = []
            result.append("")
            continue
        
        # Do not merge if it looks like a list, heading, or table row
        is_break = (
            stripped.startswith(('#', '-', '*', '1.', '|')) or 
            '|' in stripped or
            re.match(r'^\d+\.', stripped)
        )
        
        if is_break:
            if current_para:
                result.append(" ".join(current_para))
                current_para = []
            result.append(line)
        else:
            current_para.append(stripped)
            
    if current_para:
        result.append(" ".join(current_para))
        
    return "\n".join(result)

def dehyphenate(text: str) -> str:
    """
    Replace line-break hyphenation only when unambiguous.
    """
    # Look for a letter + hyphen + newline + letter
    return re.sub(r'([a-zA-Z])-\n([a-zA-Z])', r'\1\2', text)

def extract_headings(markdown: str) -> list[str]:
    """
    Return H2 headings (lines starting with ## but not TOC).
    """
    headings = []
    for line in markdown.split('\n'):
        if line.startswith('## ') and 'table of contents' not in line.lower():
            headings.append(line.lstrip('#').strip())
    return headings

def inject_toc(markdown: str, headings: list[str]) -> str:
    """
    Insert TOC after metadata header (which ends with 'Source:').
    """
    if not headings:
        return markdown
        
    toc = ["## Table of Contents (generated)"]
    for h in headings:
        toc.append(f"- {h}")
    toc_str = "\n".join(toc)
    
    # Try to insert after the metadata block
    match = re.search(r'- \*\*Source:\*\*.*?\n', markdown)
    if match:
        pos = match.end()
        return markdown[:pos] + "\n" + toc_str + "\n" + markdown[pos:]
    
    return toc_str + "\n\n" + markdown

def wrap_uncertain_tables(markdown: str) -> str:
    """
    Detect broken tables heuristically and wrap them in fenced blocks.
    """
    lines = markdown.split('\n')
    new_lines = []
    table_buffer = []

    def is_table_line(line):
        stripped = line.strip()
        if not stripped: return False
        if re.search(r'\s{3,}', stripped): return True
        if '|' in stripped: return True
        return False

    def is_likely_broken(lines_subset):
        if not lines_subset: return False
        pipe_counts = [l.count('|') for l in lines_subset if '|' in l]
        if pipe_counts and len(set(pipe_counts)) > 1:
            return True
        space_cols = [len(re.split(r'\s{3,}', l.strip())) for l in lines_subset if re.search(r'\s{3,}', l.strip())]
        if space_cols and len(set(space_cols)) > 1:
            return True
        return False

    i = 0
    while i < len(lines):
        line = lines[i]
        if is_table_line(line):
            table_buffer.append(line)
            i += 1
            while i < len(lines) and (is_table_line(lines[i]) or not lines[i].strip()):
                table_buffer.append(lines[i])
                i += 1
            
            if is_likely_broken(table_buffer):
                new_lines.append("### Table: Unlabeled")
                new_lines.append("**Table note:** Structure uncertain")
                new_lines.append("```text")
                new_lines.extend(table_buffer)
                new_lines.append("```")
            else:
                new_lines.extend(table_buffer)
            table_buffer = []
        else:
            new_lines.append(line)
            i += 1

    return "\n".join(new_lines)

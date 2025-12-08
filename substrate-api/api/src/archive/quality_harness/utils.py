"""
Utility functions for quality harness
"""

import re
from typing import List, Tuple, Optional
import nltk
from nltk.tokenize import sent_tokenize

# Try to download punkt if not available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
    except:
        pass  # Fall back to simple sentence splitting


def extract_sentences(text: str) -> List[str]:
    """Extract sentences from text"""
    try:
        # Use NLTK for better sentence splitting
        sentences = sent_tokenize(text)
    except:
        # Fallback to simple splitting
        sentences = re.split(r'[.!?]+', text)
    
    # Filter out empty sentences and clean
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    return sentences


def extract_citations(text: str) -> List[str]:
    """Extract citation markers from text"""
    # Match various citation formats: [S1], [oracle_1], etc.
    citation_pattern = re.compile(r'\[([^\]]+)\]')
    citations = citation_pattern.findall(text)
    
    # Filter to valid citation formats
    valid_citations = []
    for cite in citations:
        # Check if it's a valid citation format
        if (cite.startswith('S') and cite[1:].isdigit()) or \
           cite.startswith('oracle_') or \
           cite.startswith('block_') or \
           cite.startswith('ref_'):
            valid_citations.append(cite)
    
    return valid_citations


def compute_text_spans(
    text: str,
    max_span_length: int = 200,
    overlap: int = 50
) -> List[Tuple[str, int, int]]:
    """
    Compute text spans for citation with overlap.
    Returns list of (text, start_char, end_char) tuples.
    """
    spans = []
    sentences = extract_sentences(text)
    
    current_pos = 0
    for sentence in sentences:
        # Find sentence in original text
        sentence_start = text.find(sentence, current_pos)
        if sentence_start == -1:
            continue
        
        sentence_end = sentence_start + len(sentence)
        
        # If sentence is short enough, use as-is
        if len(sentence) <= max_span_length:
            spans.append((sentence, sentence_start, sentence_end))
        else:
            # Break long sentences into overlapping chunks
            words = sentence.split()
            chunk_words = max_span_length // 10  # Rough estimate
            
            for i in range(0, len(words), chunk_words - overlap // 10):
                chunk = ' '.join(words[i:i + chunk_words])
                chunk_start = text.find(chunk, sentence_start)
                if chunk_start != -1:
                    spans.append((chunk, chunk_start, chunk_start + len(chunk)))
        
        current_pos = sentence_end
    
    # Also add some paragraph-level spans for context
    paragraphs = text.split('\n\n')
    for para in paragraphs[:5]:  # First 5 paragraphs
        if 50 < len(para) < max_span_length * 2:
            para_start = text.find(para)
            if para_start != -1:
                spans.append((para, para_start, para_start + len(para)))
    
    # Deduplicate spans
    unique_spans = []
    seen = set()
    for span in spans:
        if span[1] not in seen:
            unique_spans.append(span)
            seen.add(span[1])
    
    # Sort by position
    unique_spans.sort(key=lambda x: x[1])
    
    return unique_spans


def calculate_edit_distance(text1: str, text2: str) -> int:
    """Calculate Levenshtein edit distance between two texts"""
    if not text1 or not text2:
        return max(len(text1), len(text2))
    
    # Simple word-level edit distance for performance
    words1 = text1.lower().split()
    words2 = text2.lower().split()
    
    m, n = len(words1), len(words2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if words1[i-1] == words2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    return dp[m][n]


def normalize_section_name(section: str) -> str:
    """Normalize section names for comparison"""
    return section.lower().replace(' ', '_').replace('-', '_')


def parse_citation_format(citation: str, format_template: str = "[S{id}]") -> Optional[str]:
    """Parse citation ID from formatted citation"""
    # Extract the ID pattern from template
    id_pattern = format_template.replace('[', r'\[').replace(']', r'\]').replace('{id}', r'(\w+)')
    match = re.match(id_pattern, citation)
    if match:
        return match.group(1)
    return None
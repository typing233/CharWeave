import re


CHAPTER_PATTERNS = [
    re.compile(r"^\s*CHAPTER\s+[IVXLCDM\d]+[\.\s]", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*Chapter\s+\d+", re.MULTILINE),
    re.compile(r"^\s*BOOK\s+(?:THE\s+)?[IVXLCDM\d]+", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*PART\s+[IVXLCDM\d]+", re.IGNORECASE | re.MULTILINE),
]

MIN_CHAPTER_LEN = 500


def split_into_chapters(text: str) -> list[str]:
    for pattern in CHAPTER_PATTERNS:
        positions = [m.start() for m in pattern.finditer(text)]
        if len(positions) >= 3:
            chapters = []
            for i, pos in enumerate(positions):
                end = positions[i + 1] if i + 1 < len(positions) else len(text)
                chunk = text[pos:end].strip()
                if len(chunk) >= MIN_CHAPTER_LEN:
                    chapters.append(chunk)
            if len(chapters) >= 3:
                return chapters

    # Fallback: split into roughly 10 equal chunks at paragraph boundaries
    target_chunks = 10
    chunk_size = len(text) // target_chunks
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        # Find nearest paragraph break after the target
        break_pos = text.find("\n\n", end)
        if break_pos == -1 or break_pos - end > chunk_size // 2:
            break_pos = end
        chunks.append(text[start:break_pos].strip())
        start = break_pos + 2

    return [c for c in chunks if len(c) >= MIN_CHAPTER_LEN]

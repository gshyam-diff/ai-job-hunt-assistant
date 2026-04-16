import io

from PyPDF2 import PdfReader

from config import CHUNK_SIZE, CHUNK_OVERLAP


def extract_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


def chunk_text(text: str) -> list[dict]:
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    index = 0

    while start < len(text):
        end = start + CHUNK_SIZE

        if end < len(text):
            boundary = text.rfind("\n", start, end)
            if boundary > start + CHUNK_SIZE // 2:
                end = boundary + 1

        chunk_content = text[start:end].strip()
        if chunk_content:
            chunks.append({
                "content": chunk_content,
                "index": index,
                "start_char": start,
                "end_char": end,
            })
            index += 1

        start = end - CHUNK_OVERLAP
        if start >= len(text):
            break

    return chunks

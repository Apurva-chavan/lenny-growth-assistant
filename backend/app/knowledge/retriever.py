"""
Lightweight knowledge base using TF-IDF (no heavy ML models).
Fits within Render free tier 512MB RAM limit.
"""
import os
import re
import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

_chunks: list["Chunk"] = []
_tfidf_index: dict = {}  # term -> {chunk_id -> tf-idf score}
_idf: dict = {}


@dataclass
class Chunk:
    id: str
    source: str
    episode_url: str
    text: str
    start_char: int
    token_estimate: int


def _tokenize(text: str) -> list[str]:
    return re.findall(r'\b[a-z]{2,}\b', text.lower())


def _chunk_text(text: str, source: str, url: str, chunk_size: int, overlap: int) -> list[Chunk]:
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        window = words[i: i + chunk_size]
        if len(window) < 20:
            break
        chunks.append(Chunk(
            id=f"{source}_{i}",
            source=source,
            episode_url=url,
            text=" ".join(window),
            start_char=i,
            token_estimate=len(window),
        ))
    return chunks


def _load_transcripts(transcripts_dir: str, chunk_size: int, overlap: int) -> list[Chunk]:
    path = Path(transcripts_dir)
    if not path.exists():
        logger.warning("transcripts_dir_missing", path=str(path))
        return []

    all_chunks = []
    for f in sorted(path.glob("*.txt")) + sorted(path.glob("*.md")):
        raw = f.read_text(encoding="utf-8", errors="ignore")
        url = ""
        lines = raw.splitlines()
        if lines and lines[0].startswith("# URL:"):
            url = lines[0].replace("# URL:", "").strip()
            raw = "\n".join(lines[1:])
        raw = re.sub(r"\s+", " ", raw).strip()
        chunks = _chunk_text(raw, f.stem, url, chunk_size, overlap)
        all_chunks.extend(chunks)
        logger.info("transcript_loaded", file=f.name, chunks=len(chunks))

    for f in path.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    raw = re.sub(r"\s+", " ", item.get("text", "")).strip()
                    chunks = _chunk_text(raw, item.get("title", f.stem), item.get("url", ""), chunk_size, overlap)
                    all_chunks.extend(chunks)
        except Exception as e:
            logger.warning("json_transcript_load_error", file=f.name, error=str(e))

    logger.info("total_chunks_loaded", count=len(all_chunks))
    return all_chunks


def _build_tfidf(chunks: list[Chunk]):
    global _tfidf_index, _idf
    N = len(chunks)
    df: dict[str, int] = {}
    tf_per_chunk: list[dict[str, float]] = []

    for chunk in chunks:
        tokens = _tokenize(chunk.text)
        counts = Counter(tokens)
        total = len(tokens) or 1
        tf = {term: count / total for term, count in counts.items()}
        tf_per_chunk.append(tf)
        for term in counts:
            df[term] = df.get(term, 0) + 1

    _idf = {term: math.log(N / (1 + freq)) for term, freq in df.items()}

    _tfidf_index = {}
    for i, (chunk, tf) in enumerate(zip(chunks, tf_per_chunk)):
        for term, tf_val in tf.items():
            score = tf_val * _idf.get(term, 0)
            if score > 0:
                if term not in _tfidf_index:
                    _tfidf_index[term] = {}
                _tfidf_index[term][i] = score


def build_index(force: bool = False):
    global _chunks
    settings = get_settings()
    _chunks = _load_transcripts(settings.transcripts_dir, settings.chunk_size, settings.chunk_overlap)
    if not _chunks:
        logger.warning("no_chunks_to_index")
        return
    _build_tfidf(_chunks)
    logger.info("index_built_and_saved", chunks=len(_chunks))


def search(query: str, top_k: int = None) -> list[Chunk]:
    global _chunks, _tfidf_index
    settings = get_settings()
    k = top_k or settings.top_k_results

    if not _chunks or not _tfidf_index:
        logger.warning("index_not_ready_for_search")
        return []

    tokens = _tokenize(query)
    scores: dict[int, float] = {}
    for token in tokens:
        if token in _tfidf_index:
            for chunk_idx, score in _tfidf_index[token].items():
                scores[chunk_idx] = scores.get(chunk_idx, 0) + score

    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    return [_chunks[i] for i, _ in top]


def get_index_stats() -> dict:
    return {
        "chunks": len(_chunks),
        "index_ready": len(_chunks) > 0 and bool(_tfidf_index),
    }

"""
Knowledge base: loads transcripts, chunks them, builds a FAISS vector index,
and provides semantic search. Uses sentence-transformers for embeddings (runs locally).
"""
import os
import json
import pickle
import re
from pathlib import Path
from dataclasses import dataclass, field
import numpy as np
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

# Lazy imports to avoid slow startup when not needed
_model = None
_index = None
_chunks: list["Chunk"] = []


@dataclass
class Chunk:
    id: str
    source: str          # filename / episode title
    episode_url: str
    text: str
    start_char: int
    token_estimate: int


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("loading_embedding_model")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("embedding_model_loaded")
    return _model


def _chunk_text(text: str, source: str, url: str, chunk_size: int, overlap: int) -> list[Chunk]:
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        window = words[i: i + chunk_size]
        if len(window) < 20:
            break
        chunk_text = " ".join(window)
        chunks.append(Chunk(
            id=f"{source}_{i}",
            source=source,
            episode_url=url,
            text=chunk_text,
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
    transcript_files = sorted(path.glob("*.txt")) + sorted(path.glob("*.md"))
    for f in transcript_files:
        raw = f.read_text(encoding="utf-8", errors="ignore")
        # Try to extract URL from first line if present (format: # URL: https://...)
        url = ""
        lines = raw.splitlines()
        if lines and lines[0].startswith("# URL:"):
            url = lines[0].replace("# URL:", "").strip()
            raw = "\n".join(lines[1:])
        # Clean whitespace
        raw = re.sub(r"\s+", " ", raw).strip()
        chunks = _chunk_text(raw, f.stem, url, chunk_size, overlap)
        all_chunks.extend(chunks)
        logger.info("transcript_loaded", file=f.name, chunks=len(chunks))

    # Also load JSON transcripts (array of {title, url, text})
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


def build_index(force: bool = False):
    """Build or load the FAISS index."""
    global _index, _chunks
    settings = get_settings()
    index_path = Path(settings.vector_index_path)
    index_file = index_path / "index.faiss"
    chunks_file = index_path / "chunks.pkl"

    if not force and index_file.exists() and chunks_file.exists():
        import faiss
        logger.info("loading_existing_index")
        _index = faiss.read_index(str(index_file))
        with open(chunks_file, "rb") as f:
            _chunks = pickle.load(f)
        logger.info("index_loaded", chunks=len(_chunks))
        return

    _chunks = _load_transcripts(settings.transcripts_dir, settings.chunk_size, settings.chunk_overlap)
    if not _chunks:
        logger.warning("no_chunks_to_index")
        return

    model = _get_model()
    texts = [c.text for c in _chunks]
    logger.info("building_embeddings", count=len(texts))
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    import faiss
    dim = embeddings.shape[1]
    _index = faiss.IndexFlatIP(dim)  # inner product = cosine on normalized vecs
    _index.add(embeddings)

    index_path.mkdir(parents=True, exist_ok=True)
    faiss.write_index(_index, str(index_file))
    with open(chunks_file, "wb") as f:
        pickle.dump(_chunks, f)
    logger.info("index_built_and_saved", chunks=len(_chunks))


def search(query: str, top_k: int = None) -> list[Chunk]:
    """Return top-k chunks most relevant to query."""
    global _index, _chunks
    settings = get_settings()
    k = top_k or settings.top_k_results

    if _index is None or not _chunks:
        logger.warning("index_not_ready_for_search")
        return []

    model = _get_model()
    q_emb = model.encode([query], normalize_embeddings=True)
    q_emb = np.array(q_emb, dtype="float32")

    scores, indices = _index.search(q_emb, k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_chunks):
            continue
        results.append(_chunks[idx])
    return results


def get_index_stats() -> dict:
    return {
        "chunks": len(_chunks),
        "index_ready": _index is not None,
    }

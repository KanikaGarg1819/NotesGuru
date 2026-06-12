"""
Syllabus Matching Service
--------------------------
Matches extracted note text to syllabus chapters using vector similarity.

How it works:
1. Convert each syllabus chapter title+description into a vector embedding
2. Convert the extracted note text into a vector embedding
3. Find the closest matching chapter using cosine similarity
4. Return the match with a confidence score (0.0 → 1.0)

Uses sentence-transformers (all-MiniLM-L6-v2) — fast, accurate, runs locally.
No API key needed for this step.
"""

import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Model (loaded once, reused for all requests) ──────────────────
_model = None

def get_model():
    """Load sentence-transformer model once and cache it."""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Model loaded successfully")
    return _model


# ── Embedding ─────────────────────────────────────────────────────

def embed_text(text: str) -> np.ndarray:
    """
    Convert text into a 384-dimensional vector embedding.
    Similar meanings → similar vectors → high cosine similarity.
    """
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.astype(np.float32)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Convert a list of texts into embeddings (batch, faster)."""
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.astype(np.float32)


# ── Similarity ────────────────────────────────────────────────────

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    Returns a score between 0.0 (no match) and 1.0 (perfect match).
    """
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


# ── Chapter Matching ──────────────────────────────────────────────

def match_note_to_chapters(
    note_text: str,
    chapters: list[dict],
    threshold: float = 0.3,
) -> dict:
    """
    Match extracted note text to the closest syllabus chapter.

    Args:
        note_text:  Extracted text from the note image
        chapters:   List of chapter dicts with keys: id, title, description
        threshold:  Minimum similarity score to count as a match (0.0-1.0)

    Returns:
        dict with:
            matched:      True if a good match was found
            chapter_id:   ID of the best matching chapter (or None)
            chapter_title: Title of the best match
            score:        Similarity score (0.0-1.0)
            all_scores:   Scores for all chapters (for debugging)
    """
    if not note_text.strip():
        return {
            "matched": False,
            "chapter_id": None,
            "chapter_title": None,
            "score": 0.0,
            "all_scores": [],
            "message": "Note text is empty",
        }

    if not chapters:
        return {
            "matched": False,
            "chapter_id": None,
            "chapter_title": None,
            "score": 0.0,
            "all_scores": [],
            "message": "No chapters provided",
        }

    # Build chapter text: combine title + description for richer matching
    chapter_texts = []
    for ch in chapters:
        title = ch.get("title", "")
        desc  = ch.get("description", "")
        combined = f"{title}. {desc}" if desc else title
        chapter_texts.append(combined)

    # Embed note text and all chapter texts
    logger.info(f"Embedding note text ({len(note_text)} chars) against {len(chapters)} chapters")
    note_embedding     = embed_text(note_text)
    chapter_embeddings = embed_texts(chapter_texts)

    # Compute similarity scores for all chapters
    scores = []
    for i, ch_embedding in enumerate(chapter_embeddings):
        score = cosine_similarity(note_embedding, ch_embedding)
        scores.append({
            "chapter_id":    chapters[i]["id"],
            "chapter_title": chapters[i]["title"],
            "score":         round(score, 4),
        })

    # Sort by score descending
    scores.sort(key=lambda x: x["score"], reverse=True)
    best = scores[0]

    logger.info(f"Best match: '{best['chapter_title']}' with score {best['score']}")

    if best["score"] < threshold:
        return {
            "matched": False,
            "chapter_id": None,
            "chapter_title": None,
            "score": best["score"],
            "all_scores": scores,
            "message": f"No strong match found (best score {best['score']} below threshold {threshold})",
        }

    return {
        "matched": True,
        "chapter_id":    best["chapter_id"],
        "chapter_title": best["chapter_title"],
        "score":         best["score"],
        "all_scores":    scores,
        "message":       "Chapter matched successfully",
    }


# ── Gap Detection ─────────────────────────────────────────────────

def detect_gaps(
    chapters: list[dict],
    matched_chapter_ids: list[int],
) -> dict:
    """
    Detect which syllabus chapters have no matched notes.

    Args:
        chapters:            All chapters in the syllabus
        matched_chapter_ids: IDs of chapters that have at least one note

    Returns:
        dict with covered and gap chapter lists + coverage percentage
    """
    matched_set = set(matched_chapter_ids)

    covered = []
    gaps    = []

    for ch in chapters:
        if ch["id"] in matched_set:
            covered.append(ch)
        else:
            gaps.append(ch)

    total    = len(chapters)
    coverage = round(len(covered) / total * 100, 1) if total > 0 else 0.0

    return {
        "total_chapters":   total,
        "covered_count":    len(covered),
        "gap_count":        len(gaps),
        "coverage_percent": coverage,
        "covered_chapters": covered,
        "gap_chapters":     gaps,
    }


# ── Embedding Storage ─────────────────────────────────────────────

def embedding_to_str(embedding: np.ndarray) -> str:
    """Convert numpy embedding to comma-separated string for DB storage."""
    return ",".join(map(str, embedding.tolist()))


def str_to_embedding(embedding_str: str) -> np.ndarray:
    """Convert stored string back to numpy embedding."""
    return np.array([float(x) for x in embedding_str.split(",")], dtype=np.float32)
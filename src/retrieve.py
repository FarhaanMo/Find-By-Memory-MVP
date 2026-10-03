"""Controlled retrieval simulation.

Token and metadata weights only. This is not Google Photos ranking.
"""

import re

STOPWORDS = {
    "a", "an", "the", "with", "my", "of", "on", "in", "and", "to", "from",
    "while", "photo", "photos", "picture", "was", "this", "for", "at", "it",
}

FIELD_WEIGHTS = (
    ("event", 8),
    ("people", 8),
    ("category", 5),
    ("association", 4),
    ("visual_detail", 3),
    ("location_context", 3),
    ("month", 2),
    ("year", 2),
    ("search_text", 3),
    ("description", 1),
)


def normalize(text):
    return re.sub(r"\s+", " ", (text or "").lower().replace("'", "")).strip()


def tokenize(text):
    parts = re.findall(r"[a-z0-9]+", normalize(text))
    return [part for part in parts if part not in STOPWORDS and len(part) > 1]


def score_photo(tokens, row):
    total = 0
    field_tokens = {name: set(tokenize(row.get(name, ""))) for name, _weight in FIELD_WEIGHTS}
    for token in tokens:
        for name, weight in FIELD_WEIGHTS:
            if token in field_tokens[name]:
                total += weight
    return total


def rank_library(memory, library):
    tokens = tokenize(memory)
    ranked = []
    for row in library:
        item = dict(row)
        item["score"] = float(score_photo(tokens, row))
        item["base_score"] = item["score"]
        ranked.append(item)
    ranked.sort(key=lambda item: (-item["score"], item["photo_id"]))
    return ranked


def initial_candidates(memory, library, limit=10):
    """Return the top overlapping cluster, usually 6 to 10 photos."""
    ranked = [row for row in rank_library(memory, library) if row["score"] > 0]
    if not ranked:
        return []
    best = ranked[0]["score"]
    selected = [row for row in ranked if row["score"] >= best * 0.72]
    if len(selected) < 6:
        selected = ranked[: min(6, len(ranked))]
    return selected[:limit]

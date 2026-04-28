import re
from typing import Iterable


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def resolve_catalog_key(query: str, candidates: Iterable[str], match_mode: str = "fuzzy") -> dict:
    candidate_list = list(candidates)
    normalized_query = normalize_text(query)

    if not normalized_query:
        return {
            "status": "not_found",
            "resolved_key": None,
            "suggestions": [],
        }

    normalized_candidates = {
        candidate: normalize_text(candidate)
        for candidate in candidate_list
    }

    exact_matches = [
        candidate
        for candidate, normalized_candidate in normalized_candidates.items()
        if normalized_candidate == normalized_query
    ]

    if len(exact_matches) == 1:
        return {
            "status": "resolved",
            "resolved_key": exact_matches[0],
            "suggestions": [],
        }

    if len(exact_matches) > 1:
        return {
            "status": "ambiguous",
            "resolved_key": None,
            "suggestions": exact_matches,
        }

    if match_mode == "exact":
        return {
            "status": "not_found",
            "resolved_key": None,
            "suggestions": [],
        }

    partial_matches = [
        candidate
        for candidate, normalized_candidate in normalized_candidates.items()
        if normalized_query in normalized_candidate
        or normalized_candidate in normalized_query
    ]

    if len(partial_matches) == 1:
        return {
            "status": "resolved",
            "resolved_key": partial_matches[0],
            "suggestions": [],
        }

    if len(partial_matches) > 1:
        return {
            "status": "ambiguous",
            "resolved_key": None,
            "suggestions": partial_matches,
        }

    return {
        "status": "not_found",
        "resolved_key": None,
        "suggestions": [],
    }

"""Scoring fusion: Q&A normalization + weighted combination + banding."""

from __future__ import annotations

from config import settings
from models import Band


def normalize_qa(raw_average: float | None) -> float | None:
    """0-5 average -> 0-100 scale (linear, per open-question #4)."""
    if raw_average is None:
        return None
    return round(raw_average / settings.qa_max_score * 100, 2)


def normalized_weights(weights: dict | None) -> dict[str, float]:
    weights = weights or {}
    resume = float(weights.get("resume", 60) or 0)
    qa = float(weights.get("qa", 40) or 0)
    total = resume + qa
    if total <= 0:
        return {"resume": 0.6, "qa": 0.4}
    return {"resume": resume / total, "qa": qa / total}


def band_for(combined: float, pass_threshold: float, hold_margin: float | None = None) -> str:
    margin = settings.hold_margin if hold_margin is None else hold_margin
    if combined >= pass_threshold:
        return Band.PASS
    if combined < pass_threshold - margin:
        return Band.REJECT
    return Band.HOLD


def fuse(
    resume_score: float | None,
    qa_score: float | None,
    weights: dict | None,
    pass_threshold: float,
) -> tuple[float, str]:
    w = normalized_weights(weights)
    combined = round(w["resume"] * (resume_score or 0) + w["qa"] * (qa_score or 0), 2)
    return combined, band_for(combined, pass_threshold)

"""answer_score: score a candidate's Q&A answer against a reference + rubric bands.

Real provider -> prompt + schema-validated JSON.
Mock provider -> deterministic overlap heuristic (offline demo/tests).
Supports rubric as a band dict {"score_5": [...], "score_3": [...], "score_0": [...]}
or a flat list.
"""

from __future__ import annotations

import json
import re

from models import Question
from schemas.llm import AnswerScoreResult

from ai.llm_client import LLMClient

SYSTEM_PROMPT = (
    "You are an assessor. Score a candidate answer against a reference answer and "
    "rubric bands. Return ONLY JSON: "
    '{"score": int 0-5, "justification": str, "confidence": float 0-1, '
    '"rubric_hits": [str]}.'
)

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you", "are",
    "was", "were", "have", "has", "had", "not", "but", "can", "will", "would",
    "into", "than", "then", "them", "they", "its", "it's", "about", "over",
    "when", "what", "which", "while", "each", "such", "also", "more", "most",
}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]{2,}", (text or "").lower())
    return {w for w in words if w not in _STOPWORDS}


def rubric_bands(rubric) -> dict[str, list[str]]:
    if isinstance(rubric, dict):
        return {k: list(v or []) for k, v in rubric.items()}
    if isinstance(rubric, list):
        return {"score_5": list(rubric), "score_3": [], "score_0": []}
    return {"score_5": [], "score_3": [], "score_0": []}


def _build_user_prompt(question: Question, answer_text: str) -> str:
    return (
        f"QUESTION: {question.text}\n"
        f"REFERENCE ANSWER: {question.reference_answer}\n"
        f"RUBRIC (bands): {json.dumps(rubric_bands(question.rubric))}\n\n"
        f"CANDIDATE ANSWER:\n{answer_text}\n\n"
        "Return the JSON object."
    )


def heuristic_answer_score(question: Question, answer_text: str) -> AnswerScoreResult:
    bands = rubric_bands(question.rubric)
    top = bands.get("score_5") or []
    mid = bands.get("score_3") or []
    criteria = top + mid

    answer_tokens = _tokens(answer_text)

    def hit(criterion: str) -> bool:
        return bool(_tokens(criterion) & answer_tokens)

    hits = [c for c in criteria if hit(c)]
    top_hits = [c for c in top if hit(c)]
    target = len(top) or len(criteria) or 1

    length_factor = min(len((answer_text or "").split()) / 25, 1.0)
    ratio = len(top_hits) / target
    raw = 5 * (0.8 * ratio + 0.2 * length_factor)
    score = int(round(max(0, min(5, raw))))
    confidence = round(min(0.95, 0.5 + 0.4 * length_factor), 2)

    if not (answer_text or "").strip():
        return AnswerScoreResult(
            score=0,
            justification="No answer provided (timeout or empty submission).",
            confidence=0.9,
            rubric_hits=[],
        )

    return AnswerScoreResult(
        score=score,
        justification=(
            f"Hit {len(top_hits)}/{len(top)} top-band rubric criteria "
            f"({len(hits)} total); answer length "
            f"{len((answer_text or '').split())} words."
        ),
        confidence=confidence,
        rubric_hits=hits,
    )


class AnswerScorer:
    def __init__(self, client: LLMClient):
        self.client = client

    def score(self, question: Question, answer_text: str) -> AnswerScoreResult:
        if self.client.is_mock:
            return heuristic_answer_score(question, answer_text)
        return self.client.complete_json(
            SYSTEM_PROMPT, _build_user_prompt(question, answer_text), AnswerScoreResult
        )
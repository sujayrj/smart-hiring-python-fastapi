"""resume_match: score a candidate résumé against a JD.

Real provider -> prompt + schema-validated JSON.
Mock provider -> deterministic keyword-overlap heuristic (offline demo/tests).
"""

from __future__ import annotations

import re

from models import JobDescription
from schemas.llm import ResumeMatchResult

from ai.llm_client import LLMClient

SYSTEM_PROMPT = (
    "You are a technical recruiter. Compare a candidate résumé against a job "
    "description and return ONLY JSON: "
    '{"score": int 0-100, "matched_skills": [str], "gaps": [str], '
    '"summary": str, "confidence": float 0-1}.'
)


def _skills(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[,\n;|]+", text or "") if s.strip()]


# Phrases that signal a skill is mentioned but not really held.
_WEAK_SIGNALS = ("no ", "not ", "limited", "learning", "basic", "some ", "little", "beginner")


def _stem(word: str) -> str:
    for suffix in ("ing", "ers", "er", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _tokens(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z0-9+#]+", (text or "").lower())}


def _skill_present(skill: str, text: str) -> bool:
    """True if every significant token of the skill appears in a sentence without a weak signal."""
    skill_tokens = [_stem(w) for w in re.findall(r"[a-z0-9]{3,}", skill.lower())]
    if not skill_tokens:
        return False
    for sentence in re.split(r"[.\n;]+", text):
        sentence_tokens = _tokens(sentence)
        if all(token in sentence_tokens for token in skill_tokens):
            return not any(weak in sentence for weak in _WEAK_SIGNALS)
    return False


def _build_user_prompt(jd: JobDescription, resume_text: str) -> str:
    return (
        f"JOB TITLE: {jd.title}\n"
        f"EXPERIENCE: {jd.experience_years}\n"
        f"MUST HAVE: {jd.must_have}\n"
        f"NICE TO HAVE: {jd.nice_to_have}\n"
        f"SUMMARY: {jd.summary}\n\n"
        f"CANDIDATE RÉSUMÉ:\n{resume_text}\n\n"
        "Return the JSON object."
    )


def heuristic_resume_match(jd: JobDescription, resume_text: str) -> ResumeMatchResult:
    must = _skills(jd.must_have)
    nice = _skills(jd.nice_to_have)
    text = (resume_text or "").lower()

    matched = [s for s in must if _skill_present(s, text)]
    gaps = [s for s in must if s not in matched]
    nice_matched = [s for s in nice if _skill_present(s, text)]

    ratio = len(matched) / len(must) if must else 0.0
    # reward must-have coverage + nice-to-haves, penalise gaps
    score = int(round(30 + 65 * ratio - 12 * len(gaps) + min(len(nice_matched), 3) * 2))
    score = max(0, min(100, score))

    length_factor = min(len(resume_text or "") / 1200, 1.0)
    confidence = round(min(0.95, 0.45 + 0.4 * length_factor + 0.1 * ratio), 2)

    if gaps:
        summary = (
            f"Matches {len(matched)}/{len(must)} must-have skills"
            f" ({', '.join(matched) or 'none'}); gaps: {', '.join(gaps)}."
        )
    else:
        summary = "Meets all must-have skills for this role."

    return ResumeMatchResult(
        score=score,
        matched_skills=matched + nice_matched,
        gaps=gaps,
        summary=summary,
        confidence=confidence,
    )


class ResumeMatcher:
    def __init__(self, client: LLMClient):
        self.client = client

    def match(self, jd: JobDescription, resume_text: str) -> ResumeMatchResult:
        if self.client.is_mock:
            return heuristic_resume_match(jd, resume_text)
        return self.client.complete_json(
            SYSTEM_PROMPT, _build_user_prompt(jd, resume_text), ResumeMatchResult
        )

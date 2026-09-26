"""Résumé screening heuristic + threshold promotion/archive rules."""

from ai.resume_match import heuristic_resume_match
from models import JobDescription
from schemas.llm import AnswerScoreResult
from ai.answer_score import heuristic_answer_score
from models import Question


def _jd() -> JobDescription:
    return JobDescription(
        id=1,
        title="Backend Engineer",
        must_have="Python, FastAPI, SQL, REST",
        nice_to_have="Docker, AWS",
        pass_threshold=70,
        confidence_cutoff=0.6,
        weights={"resume": 60, "qa": 40},
    )


def test_strong_resume_scores_higher_than_weak():
    strong = heuristic_resume_match(
        _jd(), "Python FastAPI SQL REST Docker AWS expert with years of experience."
    )
    weak = heuristic_resume_match(_jd(), "Some scripting, learning Python.")
    assert strong.score > weak.score
    assert strong.gaps == []
    assert "SQL" in weak.gaps


def test_deterministic():
    a = heuristic_resume_match(_jd(), "Python FastAPI SQL REST")
    b = heuristic_resume_match(_jd(), "Python FastAPI SQL REST")
    assert a == b


def test_answer_score_empty_is_zero():
    q = Question(id=1, text="q", reference_answer="indexes and EXPLAIN", rubric=["indexes"])
    result = heuristic_answer_score(q, "")
    assert isinstance(result, AnswerScoreResult)
    assert result.score == 0


def test_answer_score_rewards_overlap():
    q = Question(
        id=1,
        text="Optimise a slow query",
        reference_answer="Use EXPLAIN and add indexes to avoid N+1",
        rubric=["EXPLAIN", "indexes", "avoid N+1"],
    )
    good = heuristic_answer_score(q, "I would run EXPLAIN, add indexes and avoid N+1 queries.")
    poor = heuristic_answer_score(q, "Just wait longer.")
    assert good.score > poor.score
    assert "indexes" in [h.lower() for h in good.rubric_hits]

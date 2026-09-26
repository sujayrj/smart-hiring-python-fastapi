"""LLM wrapper: schema validation + exactly one retry + controlled failure."""

import pytest

from ai.llm_client import CallableProvider, LLMClient, LLMError
from schemas.llm import ResumeMatchResult

VALID = '{"score": 80, "matched_skills": ["python"], "gaps": [], "summary": "ok", "confidence": 0.9}'


def test_valid_json_is_parsed():
    client = LLMClient(CallableProvider(lambda s, u: VALID))
    result = client.complete_json("s", "u", ResumeMatchResult)
    assert result.score == 80
    assert result.matched_skills == ["python"]


def test_code_fences_are_tolerated():
    client = LLMClient(CallableProvider(lambda s, u: f"```json\n{VALID}\n```"))
    assert client.complete_json("s", "u", ResumeMatchResult).score == 80


def test_invalid_then_valid_retries_once():
    calls = {"n": 0}

    def fn(s, u):
        calls["n"] += 1
        return "not json at all" if calls["n"] == 1 else VALID

    result = LLMClient(CallableProvider(fn)).complete_json("s", "u", ResumeMatchResult)
    assert calls["n"] == 2
    assert result.score == 80


def test_invalid_after_retry_raises_controlled_error():
    calls = {"n": 0}

    def fn(s, u):
        calls["n"] += 1
        return "still not json"

    with pytest.raises(LLMError):
        LLMClient(CallableProvider(fn)).complete_json("s", "u", ResumeMatchResult)
    assert calls["n"] == 2  # never an uncontrolled loop


def test_out_of_range_is_rejected():
    bad = '{"score": 999, "matched_skills": [], "gaps": [], "summary": "", "confidence": 2.0}'
    calls = {"n": 0}

    def fn(s, u):
        calls["n"] += 1
        return bad

    with pytest.raises(LLMError):
        LLMClient(CallableProvider(fn)).complete_json("s", "u", ResumeMatchResult)
    assert calls["n"] == 2

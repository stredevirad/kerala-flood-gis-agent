# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline tests for answer checking and attempt snapshots."""

import json

import pytest

from kerala.agent import AnswerChecker, KeralaAgent


def _question(unit="count", expected_status="ok"):
    return {
        "id": "P01",
        "expected_status": expected_status,
        "expected_unit": unit,
    }


def _answer(**changes):
    answer = {
        "question_id": "P01",
        "status": "ok",
        "value": 3,
        "unit": "count",
        "parameters_used": {},
        "assumptions": "The facility point rule was applied.",
        "method": "Features were counted in the district.",
    }
    answer.update(changes)
    return answer


def test_checker_accepts_valid_count_answer():
    checker = AnswerChecker(_question(), area_of_interest_km2=100)
    assert checker.check(_answer()) == []


def test_checker_rejects_missing_keys_invalid_status_and_wrong_question():
    checker = AnswerChecker(_question(), area_of_interest_km2=100)
    assert "missing required key: method" in checker.check({"question_id": "P01"})
    assert "status must be 'ok' or 'cannot_answer'" in checker.check(_answer(status="maybe"))
    assert any(
        "question_id does not match" in issue
        for issue in checker.check(_answer(question_id="P02"))
    )


def test_checker_requires_value_and_unit_for_answerable_question():
    checker = AnswerChecker(_question(unit="km2"), area_of_interest_km2=100)
    issues = checker.check(_answer(value=None, unit="km"))
    assert "value must not be null for an answerable question" in issues
    assert "unit must equal expected unit 'km2'" in issues


@pytest.mark.parametrize("value", [True, 1.5, -1])
def test_checker_rejects_noninteger_or_negative_counts(value):
    checker = AnswerChecker(_question(), area_of_interest_km2=100)
    issues = checker.check(_answer(value=value))
    assert issues


@pytest.mark.parametrize("value", [-0.01, 100.01, float("nan"), True])
def test_checker_rejects_invalid_percentages(value):
    checker = AnswerChecker(_question(unit="percent"), area_of_interest_km2=100)
    issues = checker.check(_answer(value=value, unit="percent"))
    assert any("percent" in issue for issue in issues)


def test_checker_rejects_km2_outside_projected_area_rules():
    checker = AnswerChecker(_question(unit="km2"), area_of_interest_km2=100)
    too_small = checker.check(_answer(value=0.4, unit="km2"))
    assert "looks like an area computed in degrees or the wrong unit; work in a projected CRS" in too_small
    too_large = checker.check(_answer(value=101, unit="km2"))
    assert "km2 value exceeds the area of interest" in too_large
    assert checker.check(_answer(value=100, unit="km2")) == []


def test_checker_accepts_cannot_answer_only_with_null_value_and_unit():
    checker = AnswerChecker(_question(expected_status="cannot_answer"), area_of_interest_km2=100)
    answer = _answer(
        status="cannot_answer", value=None, unit=None,
        assumptions="The available layers do not contain evacuation records.",
    )
    assert checker.check(answer) == []
    assert any(
        "value must be null" in issue
        for issue in checker.check(_answer(status="cannot_answer", value=3, unit="count"))
    )


def test_checker_reads_json_file_and_reports_parse_errors(tmp_path):
    checker = AnswerChecker(_question(), area_of_interest_km2=100)
    answer_path = tmp_path / "answer.json"
    answer_path.write_text(json.dumps(_answer()), encoding="utf-8")
    assert checker.check_file(answer_path) == []
    answer_path.write_text("{", encoding="utf-8")
    assert "could not be read as JSON" in checker.check_file(answer_path)[0]
    assert "is missing" in checker.check_file(tmp_path / "missing.json")[0]


def test_kerala_agent_numbers_attempt_snapshots_from_one(tmp_path):
    agent = KeralaAgent(
        object(), question=_question(), arm="noparam", data_text="",
        area_of_interest_km2=100,
    )
    work_dir = tmp_path / "work"
    pred_dir = work_dir / "pred_results"
    pred_dir.mkdir(parents=True)
    answer_path = pred_dir / "answer.json"
    answer_path.write_text(json.dumps(_answer()), encoding="utf-8")

    assert agent._validate_outputs(str(work_dir)) == ""
    answer_path.write_text(json.dumps(_answer(value=-1)), encoding="utf-8")
    assert "count values must be >= 0" in agent._validate_outputs(str(work_dir))
    answer_path.unlink()
    assert "missing" in agent._validate_outputs(str(work_dir))

    attempts = work_dir / "attempts"
    assert json.loads((attempts / "answer_1.json").read_text(encoding="utf-8")) == _answer()
    assert json.loads((attempts / "answer_3.json").read_text(encoding="utf-8")) == {"missing": True}
    records = [json.loads(line) for line in (work_dir / "checker.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [record["attempt"] for record in records] == [1, 2, 3]
    assert [record["accepted"] for record in records] == [True, False, False]

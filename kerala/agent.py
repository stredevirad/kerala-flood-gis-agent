# SPDX-License-Identifier: AGPL-3.0-or-later
"""Kerala benchmark agent, output checker, and shared prompt construction."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any, Mapping

from app import data_profile
from app.runner import DATA_BLOCK, SKILLS_BLOCK, SYSTEM_PROMPT
from app.skills_store import SkillsStore
from src.agent.react_agent import GISReActAgent, _link_dataset

from kerala.pack.pack import (
    DOMAIN_PARAM_DESCRIPTION,
    bind_domain_param,
    index_text,
    load_pack,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LAYERS = ROOT / "data" / "kerala" / "layers"
PROFILE_ROOT = ROOT / "results" / "_profile"
ANSWER_FIELDS = (
    "question_id", "status", "value", "unit", "parameters_used", "assumptions", "method"
)
VALID_STATUSES = {"ok", "cannot_answer"}


def _question_id(question: Mapping[str, Any]) -> str:
    return str(question.get("id", question.get("question_id", "")))


class AnswerChecker:
    """Check answer structure and unit/range constraints without pack values."""

    def __init__(self, question: Mapping[str, Any], area_of_interest_km2: float):
        self.question = dict(question)
        self.question_id = _question_id(question)
        self.expected_status = question.get("expected_status", "ok")
        self.expected_unit = question.get("expected_unit")
        self.area_of_interest_km2 = float(area_of_interest_km2)

    def check(self, answer: Any) -> list[str]:
        if not isinstance(answer, dict):
            return ["answer.json must contain a JSON object"]
        issues = [f"missing required key: {key}" for key in ANSWER_FIELDS if key not in answer]
        if issues:
            return issues

        if answer["question_id"] != self.question_id:
            issues.append("question_id does not match the requested question")
        if not isinstance(answer["status"], str) or answer["status"] not in VALID_STATUSES:
            issues.append("status must be 'ok' or 'cannot_answer'")
            return issues
        if not isinstance(answer["parameters_used"], dict):
            issues.append("parameters_used must be an object")
        if not isinstance(answer["assumptions"], str):
            issues.append("assumptions must be a string")
        if not isinstance(answer["method"], str):
            issues.append("method must be a string")

        status = answer["status"]
        value = answer["value"]
        unit = answer["unit"]
        if status == "cannot_answer":
            if value is not None:
                issues.append("value must be null when status is cannot_answer")
            if unit is not None:
                issues.append("unit must be null when status is cannot_answer")
            return issues

        if value is None:
            issues.append("value must not be null when status is ok")
        if self.expected_status == "ok":
            if unit != self.expected_unit:
                issues.append(f"unit must equal expected unit {self.expected_unit!r}")

        if unit == "count":
            if isinstance(value, bool) or not isinstance(value, int):
                issues.append("count values must be integers")
            elif value < 0:
                issues.append("count values must be >= 0")
        elif unit == "percent":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                issues.append("percent values must be numeric")
            elif not math.isfinite(float(value)) or not 0 <= float(value) <= 100:
                issues.append("percent values must be between 0 and 100")
        elif unit == "km2":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                issues.append("km2 values must be numeric")
            elif not math.isfinite(float(value)):
                issues.append("km2 values must be finite")
            elif value < 1:
                issues.append(
                    "looks like an area computed in degrees or the wrong unit; work in a projected CRS"
                )
            elif value > self.area_of_interest_km2:
                issues.append("km2 value exceeds the area of interest")
        return issues

    def check_file(self, path: str | Path) -> list[str]:
        answer_path = Path(path)
        if not answer_path.is_file():
            return ["pred_results/answer.json is missing"]
        try:
            answer = json.loads(answer_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return [f"answer.json could not be read as JSON: {exc}"]
        return self.check(answer)


class KeralaAgent(GISReActAgent):
    """GISclaw ReAct agent with answer snapshots and the pack-free checker."""

    def __init__(
        self,
        llm_engine,
        *,
        question: Mapping[str, Any],
        arm: str,
        data_text: str,
        area_of_interest_km2: float,
        pack: Mapping[str, Any] | None = None,
        timeout: int = 300,
        max_rounds: int = 12,
        context_chars: int = 24_000,
        verbose: bool = False,
        extra_tools: dict | None = None,
    ):
        if arm not in {"noparam", "inline", "pack"}:
            raise ValueError(f"Unknown benchmark arm: {arm}")
        if arm == "pack" and pack is None:
            pack = load_pack()
        self.question = dict(question)
        self.arm = arm
        self.data_text = data_text
        self.pack = pack
        self.answer_checker = AnswerChecker(question, area_of_interest_km2)
        self._answer_attempt = 0
        self._run_work_dir: Path | None = None

        tools = dict(extra_tools or {})
        prompt_builder = lambda tool_descriptions: build_system_prompt(
            tool_descriptions=tool_descriptions,
            arm=self.arm,
            needs_params=self.question.get("needs_params", []),
            data_text=self.data_text,
            pack=self.pack,
        )
        super().__init__(
            llm_engine=llm_engine,
            timeout=timeout,
            max_rounds=max_rounds,
            verbose=verbose,
            system_prompt_builder=prompt_builder,
            extra_tools=tools,
            context_chars=context_chars,
        )

    def run(self, instruction: str, data_dir: str, work_dir: str, on_step=None, should_stop=None):
        self._run_work_dir = Path(work_dir)
        if self.arm == "pack":
            if self.pack is None:
                raise RuntimeError("pack arm requires a validated domain pack")
            self.extra_tools["domain_param"] = (
                bind_domain_param(self.pack, self._run_work_dir), DOMAIN_PARAM_DESCRIPTION
            )
        return super().run(
            instruction=instruction,
            data_dir=data_dir,
            work_dir=work_dir,
            on_step=on_step,
            should_stop=should_stop,
        )

    def _validate_outputs(self, work_dir: str) -> str:
        root = Path(work_dir)
        answer_path = root / "pred_results" / "answer.json"
        attempts_dir = root / "attempts"
        attempts_dir.mkdir(parents=True, exist_ok=True)
        self._answer_attempt += 1
        snapshot = attempts_dir / f"answer_{self._answer_attempt}.json"
        if answer_path.is_file():
            shutil.copyfile(answer_path, snapshot)
        else:
            snapshot.write_text('{"missing": true}\n', encoding="utf-8")

        output_guard_issues = super()._validate_outputs(work_dir)
        answer_issues = self.answer_checker.check_file(answer_path)
        issues = []
        if output_guard_issues:
            issues.append(output_guard_issues)
        issues.extend(f"- {issue}" for issue in answer_issues)
        event = {
            "attempt": self._answer_attempt,
            "accepted": not issues,
            "output_guard_issues": output_guard_issues.splitlines() if output_guard_issues else [],
            "answer_issues": answer_issues,
        }
        log_path = root / "checker.jsonl"
        with log_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        return "\n".join(issues)

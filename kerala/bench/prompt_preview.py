# SPDX-License-Identifier: AGPL-3.0-or-later
"""Save a rendered Kerala agent prompt without making a model call."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from kerala.agent import build_data_text, compose_full_prompt
from kerala.config import ROOT
from kerala.pack.pack import load_pack


QUESTIONS = ROOT / "kerala" / "bench" / "questions.yaml"


def save_prompt(qid: str, arm: str, output: Path) -> str:
    entries = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))["questions"]
    question = next((entry for entry in entries if entry["id"] == qid), None)
    if question is None:
        raise ValueError(f"Unknown question ID: {qid}")
    prompt = compose_full_prompt(
        question=question,
        arm=arm,
        data_text=build_data_text(),
        pack=load_pack(),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(prompt + "\n", encoding="utf-8")
    return prompt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qid", required=True)
    parser.add_argument("--arm", required=True, choices=("noparam", "inline", "pack"))
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    prompt = save_prompt(args.qid, args.arm, args.out)
    contains_path = "dataset/" in prompt
    print(f"Saved {args.qid}/{args.arm} prompt to {args.out}")
    print(f'Contains "dataset/": {contains_path}')
    if not contains_path:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

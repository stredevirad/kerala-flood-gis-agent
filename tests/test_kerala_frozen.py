# SPDX-License-Identifier: AGPL-3.0-or-later
"""Integrity guard for Kirito-approved Kerala benchmark assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FROZEN_PATH = ROOT / "kerala" / "bench" / "frozen.json"
LAYERS = ROOT / "data" / "kerala" / "layers"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def test_frozen_assets_match_kirito_approved_hashes_and_layer_listing():
    frozen = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    assert frozen["schema_version"] == 1
    assert frozen["frozen_after"] == "gold approved"

    for relative, expected_hash in frozen["frozen_files"].items():
        path = ROOT / relative
        assert path.is_file(), f"missing frozen file: {relative}"
        assert _sha256(path) == expected_hash, f"frozen file changed: {relative}"

    expected_layers = frozen["layers"]
    actual_names = sorted(path.name for path in LAYERS.iterdir() if path.is_file())
    assert actual_names == [entry["name"] for entry in expected_layers]
    for entry in expected_layers:
        path = LAYERS / entry["name"]
        assert path.stat().st_size == entry["bytes"], f"layer size changed: {entry['name']}"
        assert _sha256(path) == entry["sha256"], f"layer hash changed: {entry['name']}"

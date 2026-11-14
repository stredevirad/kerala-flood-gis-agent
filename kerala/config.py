# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small, explicit configuration readers for KeralaFloodBench runners."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODELS_PATH = ROOT / "kerala" / "models.yaml"
ENV_PATH = ROOT / "kerala" / ".env"


def load_models(path: Path = MODELS_PATH) -> dict[str, dict[str, Any]]:
    """Read model settings without placing secret values in the environment."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not {"local-qwen7b", "cloud-flashlite", "stub"}.issubset(data):
        raise ValueError("models.yaml must define local-qwen7b, cloud-flashlite, and stub")
    return {str(key): dict(value) for key, value in data.items() if isinstance(value, dict)}


def read_env(path: Path = ENV_PATH) -> dict[str, str]:
    """Parse the ignored key file without mutating os.environ."""
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def model_config(name: str) -> dict[str, Any]:
    """Return a copy of one declared model entry."""
    try:
        return dict(load_models()[name])
    except KeyError as exc:
        raise ValueError(f"Unknown Kerala benchmark model: {name}") from exc

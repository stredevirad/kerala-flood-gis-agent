# SPDX-License-Identifier: AGPL-3.0-or-later
"""Schema validation and tool access for the Kerala domain parameter pack."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Any, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACK_PATH = Path(__file__).with_name("kerala_pack.yaml")
DEFAULT_MANIFEST_PATH = ROOT / "data" / "kerala" / "meta" / "data_manifest.json"
PARAMETER_FIELDS = {
    "value", "unit", "description", "kind", "provenance", "rationale", "plausible_range"
}
KINDS = {"calibrated", "standard_practice", "project_convention"}
EXPECTED_KEYS = (
    "project_crs",
    "flood_date",
    "water_threshold_vv_db",
    "permanent_water_rule",
    "max_flood_slope_deg",
    "low_lying_max_elevation_m",
    "relief_camp_hospital_access_m",
    "facility_point_rule",
    "raster_area_rule",
)
DOMAIN_PARAM_DESCRIPTION = (
    "\n\n8. domain_param(key)\n"
    "   Retrieve one sourced parameter from the Kerala domain pack. "
    "Use the exact parameter key; this tool records each call."
)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Domain pack not found: {path}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("Domain pack must be a YAML mapping")
    return loaded


def _validate_structure(raw: Mapping[str, Any]) -> dict[str, Any]:
    if raw.get("schema_version") != 1:
        raise ValueError("Domain pack schema_version must be 1")
    parameters = raw.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("Domain pack parameters must be a mapping")
    if set(parameters) != set(EXPECTED_KEYS):
        missing = sorted(set(EXPECTED_KEYS) - set(parameters))
        extra = sorted(set(parameters) - set(EXPECTED_KEYS))
        raise ValueError(f"Domain pack keys differ from schema; missing={missing}, extra={extra}")

    checked: dict[str, Any] = {}
    for key in EXPECTED_KEYS:
        entry = parameters[key]
        if not isinstance(entry, dict):
            raise ValueError(f"{key} must be a mapping")
        if set(entry) != PARAMETER_FIELDS:
            missing = sorted(PARAMETER_FIELDS - set(entry))
            extra = sorted(set(entry) - PARAMETER_FIELDS)
            raise ValueError(f"{key} fields differ from schema; missing={missing}, extra={extra}")
        if entry["kind"] not in KINDS:
            raise ValueError(f"{key}.kind must be one of {sorted(KINDS)}")
        for field in ("unit", "description", "provenance", "rationale"):
            if not isinstance(entry[field], str) or not entry[field].strip():
                raise ValueError(f"{key}.{field} must be a non-empty string")
        if "\n" in entry["description"] or "\r" in entry["description"]:
            raise ValueError(f"{key}.description must be one line")
        plausible = entry["plausible_range"]
        if plausible is not None:
            if (
                not isinstance(plausible, list)
                or len(plausible) != 2
                or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in plausible)
                or not all(math.isfinite(float(value)) for value in plausible)
                or float(plausible[0]) > float(plausible[1])
            ):
                raise ValueError(f"{key}.plausible_range must be null or an ordered numeric pair")
        checked[key] = dict(entry)
    return checked


def load_pack(
    pack_path: str | Path | None = None,
    manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate the pack, resolving its calibrated T from the manifest."""
    source = Path(pack_path) if pack_path is not None else DEFAULT_PACK_PATH
    raw = _read_yaml(source)
    parameters = _validate_structure(raw)
    threshold = parameters["water_threshold_vv_db"]["value"]
    if threshold is None:
        manifest_file = Path(manifest_path) if manifest_path is not None else DEFAULT_MANIFEST_PATH
        if not manifest_file.is_file():
            raise FileNotFoundError(
                f"Water threshold is unresolved: Phase 2 manifest is missing at {manifest_file}"
            )
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        if "T" not in manifest:
            raise ValueError("Phase 2 manifest has no rounded Otsu threshold field T")
        threshold = manifest["T"]
        parameters["water_threshold_vv_db"]["value"] = threshold

    for key, entry in parameters.items():
        value = entry["value"]
        if value is None:
            raise ValueError(f"{key}.value is unresolved")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{key}.value must be finite")
        plausible = entry["plausible_range"]
        if plausible is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{key}.value must be numeric for its plausible range")
            if not float(plausible[0]) <= float(value) <= float(plausible[1]):
                raise ValueError(
                    f"{key}.value {value} is outside plausible_range {plausible}"
                )
    return {"schema_version": 1, "parameters": parameters}


def index_text(keys, pack: Mapping[str, Any] | None = None, pack_path=None) -> str:
    """Return descriptions only for the requested keys; never include values."""
    raw = _read_yaml(Path(pack_path) if pack_path is not None else DEFAULT_PACK_PATH)
    parameters = pack["parameters"] if pack is not None else _validate_structure(raw)
    selected = []
    for key in keys:
        if key not in parameters:
            raise KeyError(f"Unknown domain parameter key: {key}")
        selected.append(f"- {key}: {parameters[key]['description']}")
    return "\n".join(selected)


def _append_call(work_dir: str | Path | None, key: str, known: bool) -> None:
    if work_dir is None:
        return
    path = Path(work_dir) / "pack_calls.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {"time": datetime.now(timezone.utc).isoformat(), "key": key, "known": known}
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")


def domain_param(
    key: str = "",
    *,
    pack: Mapping[str, Any] | None = None,
    work_dir: str | Path | None = None,
) -> str:
    """Return a sourced parameter or the available key list, recording each call."""
    normalized = key.strip() if isinstance(key, str) else ""
    try:
        if pack is None:
            declared = _validate_structure(_read_yaml(DEFAULT_PACK_PATH))
            if not normalized or normalized not in declared:
                _append_call(work_dir, normalized, False)
                return "Available domain parameter keys: " + ", ".join(declared)
            current = load_pack()
        else:
            current = pack
        parameters = current["parameters"]
        if not normalized or normalized not in parameters:
            _append_call(work_dir, normalized, False)
            return "Available domain parameter keys: " + ", ".join(parameters)
        _append_call(work_dir, normalized, True)
        entry = parameters[normalized]
        return json.dumps(
            {
                "key": normalized,
                "value": entry["value"],
                "unit": entry["unit"],
                "kind": entry["kind"],
                "provenance": entry["provenance"],
                "rationale": entry["rationale"],
            },
            ensure_ascii=False,
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        _append_call(work_dir, normalized, False)
        return f"Domain pack unavailable: {exc}"


def bind_domain_param(pack: Mapping[str, Any], work_dir: str | Path):
    """Bind a validated pack and per-run call log path to the GISclaw tool."""
    return partial(domain_param, pack=pack, work_dir=work_dir)

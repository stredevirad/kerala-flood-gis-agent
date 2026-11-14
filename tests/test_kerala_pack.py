# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline tests for the Kerala domain parameter pack."""

import json

import pytest

from kerala.pack.pack import bind_domain_param, index_text, load_pack


def _manifest(path, threshold=-18.4):
    path.write_text(json.dumps({"T": threshold}), encoding="utf-8")
    return path


def test_schema_v1_resolves_calibrated_threshold(tmp_path):
    manifest = _manifest(tmp_path / "manifest.json")
    pack = load_pack(manifest_path=manifest)

    assert pack["schema_version"] == 1
    assert len(pack["parameters"]) == 10
    threshold = pack["parameters"]["water_threshold_vv_db"]
    assert threshold["value"] == -18.4
    assert threshold["kind"] == "calibrated"
    facility_buffer = pack["parameters"]["facility_flood_buffer_m"]
    assert facility_buffer["value"] == 250
    assert facility_buffer["unit"] == "m"
    assert facility_buffer["kind"] == "project_convention"
    assert facility_buffer["plausible_range"] == [50, 1000]
    for parameter in pack["parameters"].values():
        assert set(parameter) == {
            "value", "unit", "description", "kind", "provenance", "rationale", "plausible_range"
        }


def test_missing_manifest_keeps_threshold_unresolved(tmp_path):
    with pytest.raises(FileNotFoundError, match="Water threshold is unresolved"):
        load_pack(manifest_path=tmp_path / "missing.json")


def test_manifest_threshold_outside_declared_range_is_rejected(tmp_path):
    manifest = _manifest(tmp_path / "manifest.json", threshold=-11.6)
    with pytest.raises(ValueError, match="outside plausible_range"):
        load_pack(manifest_path=manifest)


def test_index_text_lists_only_requested_keys_and_no_values(tmp_path):
    pack = load_pack(manifest_path=_manifest(tmp_path / "manifest.json"))
    text = index_text(
        ["water_threshold_vv_db", "max_flood_slope_deg", "facility_flood_buffer_m"], pack=pack
    )

    assert "water_threshold_vv_db" in text
    assert "max_flood_slope_deg" in text
    assert "facility_flood_buffer_m" in text
    assert "project_crs" not in text
    assert "-18.4" not in text
    assert "5 degree" not in text
    assert "250" not in text


def test_domain_param_returns_provenance_and_logs_every_call(tmp_path):
    pack = load_pack(manifest_path=_manifest(tmp_path / "manifest.json"))
    tool = bind_domain_param(pack, tmp_path)

    threshold = json.loads(tool(key="water_threshold_vv_db"))
    assert threshold["value"] == -18.4
    assert threshold["unit"] == "dB"
    assert threshold["kind"] == "calibrated"
    assert threshold["provenance"]
    assert threshold["rationale"]

    unknown = tool(key="not_a_parameter")
    empty = tool()
    assert "Available domain parameter keys:" in unknown
    assert "water_threshold_vv_db" in empty

    events = [json.loads(line) for line in (tmp_path / "pack_calls.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(events) == 3
    assert [event["key"] for event in events] == [
        "water_threshold_vv_db", "not_a_parameter", ""
    ]
    assert [event["known"] for event in events] == [True, False, False]

# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline tests for controlled prompts and dataset boundary isolation."""

import json

from kerala.agent import build_data_text, build_system_prompt, compose_full_prompt, compose_task
from kerala.pack.pack import DOMAIN_PARAM_DESCRIPTION, bind_domain_param, load_pack
from src.agent.react_agent import _link_dataset


LAYER_NAMES = {
    "districts.gpkg",
    "taluks.gpkg",
    "hospitals.geojson",
    "schools.geojson",
    "roads_major.gpkg",
    "s1_vv_20180821_db.tif",
    "jrc_seasonality.tif",
    "dem_cop30.tif",
    "flood_extent_20180821.gpkg",
}


def _pack(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"T": -18.4}), encoding="utf-8")
    return load_pack(manifest_path=manifest_path)


def _question():
    return {
        "id": "P05",
        "text": "What area was classified as water from the Sentinel-1 VV raster?",
        "needs_params": ["water_threshold_vv_db"],
        "expected_unit": "km2",
    }


def _facility_question():
    return {
        "id": "P01",
        "text": "How many hospitals were flood-affected?",
        "needs_params": ["facility_point_rule", "facility_flood_buffer_m"],
        "expected_unit": "count",
    }


def test_system_prompts_differ_only_by_pack_index(tmp_path):
    pack = _pack(tmp_path)
    tools = "Shared GIS tools." + DOMAIN_PARAM_DESCRIPTION
    common = {
        "tool_descriptions": tools,
        "needs_params": ["water_threshold_vv_db"],
        "data_text": "- dataset/s1_vv_20180821_db.tif — raster, one band, EPSG:32643",
        "pack": pack,
        "skills_text": "",
    }
    prompts = {
        arm: build_system_prompt(arm=arm, **common)
        for arm in ("noparam", "inline", "pack")
    }
    assert prompts["noparam"] == prompts["inline"]
    assert "dataset/s1_vv_20180821_db.tif" in prompts["noparam"]
    assert prompts["pack"].startswith(prompts["noparam"])
    pack_tail = prompts["pack"][len(prompts["noparam"]):]
    assert pack_tail.startswith("\n\n## Domain pack (Kerala 2018)")
    assert "-18.4" not in prompts["pack"]


def test_tasks_differ_only_in_parameter_section_and_a2_has_values(tmp_path):
    pack = _pack(tmp_path)
    question = _question()
    tasks = {
        arm: compose_task(question, arm, pack=pack)
        for arm in ("noparam", "inline", "pack")
    }
    pieces = {arm: task.split("\n\n") for arm, task in tasks.items()}
    assert pieces["noparam"][0] == pieces["inline"][0] == pieces["pack"][0]
    assert pieces["noparam"][2] == pieces["inline"][2] == pieces["pack"][2]
    assert pieces["noparam"][1] != pieces["inline"][1] != pieces["pack"][1]
    assert "water_threshold_vv_db = -18.4 dB" in pieces["inline"][1]
    assert pieces["noparam"][2] == pieces["inline"][2] == pieces["pack"][2]
    assert "All input files are in dataset/ (e.g. dataset/districts.gpkg). Write every output to pred_results/." in pieces["noparam"][2]
    assert 'Use the execute tool with this 3-line Python example' in pieces["noparam"][2]
    assert 'json.dump(answer, f, ensure_ascii=False, indent=2)' in pieces["noparam"][2]
    assert "-18.4" not in tasks["noparam"]
    assert "-18.4" not in tasks["pack"]


def test_facility_buffer_value_is_inline_only(tmp_path):
    pack = _pack(tmp_path)
    question = _facility_question()
    tasks = {arm: compose_task(question, arm, pack=pack) for arm in ("noparam", "inline", "pack")}
    assert "facility_flood_buffer_m = 250 m" in tasks["inline"]
    assert "250 m" not in tasks["noparam"]
    assert "250 m" not in tasks["pack"]
    system = build_system_prompt(
        "Shared GIS tools." + DOMAIN_PARAM_DESCRIPTION,
        "pack",
        question["needs_params"],
        "",
        pack=pack,
        skills_text="",
    )
    assert "facility_flood_buffer_m" in system
    assert "250" not in system


def test_prompts_tasks_do_not_leak_metadata_or_threshold_outside_a2(tmp_path):
    pack = _pack(tmp_path)
    tools = "Shared GIS tools." + DOMAIN_PARAM_DESCRIPTION
    for arm in ("noparam", "inline", "pack"):
        system = build_system_prompt(
            tools, arm, _question()["needs_params"], "- dataset/s1_vv_20180821_db.tif", pack, skills_text=""
        )
        task = compose_task(_question(), arm, pack=pack)
        combined = (system + "\n" + task).casefold()
        assert "all input files are in dataset/" in combined
        assert "write every output to pred_results/" in combined
        assert 'open("pred_results/answer.json", "w", encoding="utf-8")' in combined
        assert "dataset/s1_vv_20180821_db.tif" in combined
        assert "manifest" not in combined
        assert "flood_mask" not in combined
        assert "quicklook" not in combined
        if arm == "inline":
            assert "-18.4" in task
            assert "-18.4" not in system
        else:
            assert "-18.4" not in combined


def test_pack_control_question_has_empty_parameter_section(tmp_path):
    pack = _pack(tmp_path)
    control = {"id": "C01", "text": "Compute total district area.", "needs_params": []}
    tasks = [compose_task(control, arm, pack=pack) for arm in ("noparam", "inline", "pack")]
    assert tasks[0] == tasks[1] == tasks[2]
    prompt = build_system_prompt(
        "Shared GIS tools." + DOMAIN_PARAM_DESCRIPTION,
        "pack", [], "", pack=pack, skills_text="",
    )
    assert "This question needs no pack parameters." in prompt


def test_domain_tool_is_value_gated_outside_pack_arm(tmp_path):
    pack = _pack(tmp_path)
    disabled = bind_domain_param(pack, tmp_path / "noparam", allow_values=False)
    enabled = bind_domain_param(pack, tmp_path / "pack", allow_values=True)

    no_value = disabled(key="water_threshold_vv_db")
    value = enabled(key="water_threshold_vv_db")
    assert "-18.4" not in no_value
    assert "-18.4" in value


def test_dataset_link_exposes_only_the_nine_layer_files(tmp_path):
    source = tmp_path / "layers"
    source.mkdir()
    for name in LAYER_NAMES:
        (source / name).write_bytes(b"offline fixture")
    work = tmp_path / "work"
    work.mkdir()
    dataset = work / "dataset"
    _link_dataset(str(source), str(dataset))

    assert {path.name for path in dataset.iterdir()} == LAYER_NAMES
    assert not {"meta", "bench", "pack", "manifest", "cache"}.intersection(
        path.name for path in dataset.iterdir()
    )


def test_data_profile_block_is_saved_outside_dataset(tmp_path):
    data_dir = tmp_path / "layers"
    data_dir.mkdir()
    (data_dir / "points.geojson").write_text(
        '{"type":"FeatureCollection","features":[]}', encoding="utf-8"
    )
    profile_root = tmp_path / "_profile"

    block = build_data_text(data_dir=data_dir, profile_root=profile_root)

    assert "dataset/points.geojson" in block
    assert "- points.geojson" not in block
    assert (profile_root / "data_block.txt").read_text(encoding="utf-8") == block
    assert (profile_root / "data").is_dir()


def test_preview_combines_the_actual_system_prompt_and_task(tmp_path):
    pack = _pack(tmp_path)
    data_text = "- dataset/districts.gpkg — vector, 2 features, Polygon, CRS EPSG:32643"
    prompt = compose_full_prompt(_facility_question(), "noparam", data_text, pack=pack)

    assert prompt.startswith("## SYSTEM PROMPT\n")
    assert "## TASK\nHow many hospitals were flood-affected?" in prompt
    assert "dataset/districts.gpkg" in prompt
    assert "All input files are in dataset/" in prompt

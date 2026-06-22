#!/usr/bin/env python3
"""Process one 2026 instruction PDF from R2 through the Instruction V2 pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

ROOT_DIR = Path(__file__).resolve().parents[2]
AGENT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from harvest_pdfs import (  # noqa: E402
    DEFAULT_R2_BUCKET,
    DEFAULT_YEAR,
    create_r2_client,
    load_r2_config,
    r2_bucket_name,
)
from ingest_2026 import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    list_r2_pdfs,
    load_r2_inventory_cache,
)
from instruction_metadata import (  # noqa: E402
    PIPELINE_STOPPOINTS,
    build_metadata_record,
    instruction_id_for,
    load_jsonl_manifest,
    merge_metadata,
    needs_pipeline_run,
    pdf_filename_for,
    save_jsonl_manifest,
    stoppoint_rank,
    utc_now_iso,
)

TEMP_INSTRUCTIONS_DIR = ROOT_DIR / "temp" / "instructions"
RUNS_DIR = ROOT_DIR / "runs"
DEFAULT_BAG = 1

LAST_STAGE_FOR_STOPPOINT = {
    "phase1": "phase1_pdf_pages",
    "step-map": "stage4b_rendered_glyph_corruption_diagnostics",
    "crop-cache": "stage5e_export_crop_cache",
    "qty": "stage6_qty_ocr",
    "segmentation": "stage7_part_segmentation",
}

BANNED_SCRIPTS = (
    "stage5_orchestrator.py",
    "stage5f_callout_quality.py",
)

RUN_INDEX_FILES_BY_STOPPOINT: dict[str, dict[str, str]] = {
    "phase1": {
        "set_context": "indexes/00_set_context.json",
        "pdf_manifest": "indexes/01_pdf_manifest.json",
        "page_index": "indexes/02_page_index.json",
    },
    "step-map": {
        "bag_candidates": "indexes/03_bag_candidates.json",
        "bag_gap_review": "indexes/03b_bag_gap_review.json",
        "bag_map": "indexes/04_bag_map.json",
        "step_map": "indexes/05_step_map.json",
        "step_map_diagnostics": "indexes/05a_v1_step_detections.json",
        "glyph_corruption_diagnostics": "diagnostics/step_map_rendered_glyph_corruption.json",
    },
    "crop-cache": {
        "callout_crop_box_map": "indexes/06_callout_crop_box_map.json",
        "sequence_completeness": "indexes/06a_sequence_completeness_diagnostics.json",
    },
    "qty": {
        "qty_ocr_map": "indexes/07_qty_ocr_map.json",
    },
    "segmentation": {
        "part_segmentation_map": "indexes/08_part_segmentation_map.json",
    },
}

STAGE_INDEX_REL_PATHS: dict[str, dict[str, str]] = {
    "stage0_set_context": {"set_context": "indexes/00_set_context.json"},
    "phase1_pdf_pages": {
        "pdf_manifest": "indexes/01_pdf_manifest.json",
        "page_index": "indexes/02_page_index.json",
    },
    "stage2_bag_candidates": {"bag_candidates": "indexes/03_bag_candidates.json"},
    "stage3b_bag_gap_review": {"bag_gap_review": "indexes/03b_bag_gap_review.json"},
    "stage3_bag_map": {"bag_map": "indexes/04_bag_map.json"},
    "stage4_step_map": {"step_map": "indexes/05_step_map.json"},
    "stage4b_rendered_glyph_corruption_diagnostics": {
        "glyph_corruption_diagnostics": "diagnostics/step_map_rendered_glyph_corruption.json",
    },
    "stage5_callout_crop_boxes": {"callout_crop_box_map": "indexes/06_callout_crop_box_map.json"},
    "stage5d_sequence_completeness_diagnostics": {
        "sequence_completeness": "indexes/06a_sequence_completeness_diagnostics.json",
    },
    "stage6_qty_ocr": {"qty_ocr_map": "indexes/07_qty_ocr_map.json"},
    "stage7_part_segmentation": {"part_segmentation_map": "indexes/08_part_segmentation_map.json"},
}


@dataclass(frozen=True)
class Stage:
    key: str
    script: str
    stoppoint: str
    build_cmd: Callable[["WorkerConfig"], Sequence[str]]


@dataclass
class WorkerConfig:
    set_num: str
    pdf: Path
    run_id: str
    bag: int
    stoppoint: str
    workspace: "RunWorkspace"


@dataclass(frozen=True)
class RunWorkspace:
    set_num: str
    run_id: str
    root: Path

    @classmethod
    def for_set(cls, set_num: str) -> "RunWorkspace":
        run_id = run_id_for(set_num)
        return cls(set_num=set_num, run_id=run_id, root=RUNS_DIR / set_num)

    @property
    def rel(self) -> str:
        return str(self.root.relative_to(ROOT_DIR))

    @property
    def indexes_dir(self) -> Path:
        return self.root / "indexes"

    @property
    def diagnostics_dir(self) -> Path:
        return self.root / "diagnostics"

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        (self.root / "pages").mkdir(parents=True, exist_ok=True)
        (self.root / "pdfs").mkdir(parents=True, exist_ok=True)
        self.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        (self.root / "debug").mkdir(parents=True, exist_ok=True)

    def path(self, rel: str) -> Path:
        return self.root / rel

    def rel_path(self, path: Path) -> str:
        return str(path.relative_to(ROOT_DIR))

    def subprocess_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["A2B_RUN_DIR"] = self.rel
        return env


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_set_id(raw: str) -> str:
    value = str(raw or "").strip()
    if not value:
        return value
    if "-" not in value:
        return f"{value}-1"
    return value


def run_id_for(set_num: str) -> str:
    return str(set_num).strip()


def local_temp_path_for(set_num: str) -> Path:
    return TEMP_INSTRUCTIONS_DIR / set_num / pdf_filename_for(set_num)


def download_r2_pdf(client, bucket: str, r2_key: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(bucket, r2_key, str(dest))


def _all_stages() -> list[Stage]:
    return [
        Stage(
            key="stage0_set_context",
            script="stage0_set_context.py",
            stoppoint="phase1",
            build_cmd=lambda cfg: ["--set-num", cfg.set_num],
        ),
        Stage(
            key="phase1_pdf_pages",
            script="phase1_pdf_pages.py",
            stoppoint="phase1",
            build_cmd=lambda cfg: [
                "--pdf",
                str(cfg.pdf),
                "--run-id",
                cfg.run_id,
            ],
        ),
        Stage(
            key="stage2_bag_candidates",
            script="stage2_bag_candidates.py",
            stoppoint="step-map",
            build_cmd=lambda _cfg: [],
        ),
        Stage(
            key="stage3b_bag_gap_review",
            script="stage3b_bag_gap_review.py",
            stoppoint="step-map",
            build_cmd=lambda _cfg: [],
        ),
        Stage(
            key="stage3_bag_map",
            script="stage3_bag_map.py",
            stoppoint="step-map",
            build_cmd=lambda _cfg: [],
        ),
        Stage(
            key="stage4_step_map",
            script="stage4_step_map.py",
            stoppoint="step-map",
            build_cmd=lambda _cfg: [],
        ),
        Stage(
            key="stage4b_rendered_glyph_corruption_diagnostics",
            script="stage4b_rendered_glyph_corruption_diagnostics.py",
            stoppoint="step-map",
            build_cmd=lambda _cfg: [],
        ),
        Stage(
            key="stage5_callout_crop_boxes",
            script="stage5_callout_crop_boxes.py",
            stoppoint="crop-cache",
            build_cmd=lambda _cfg: [],
        ),
        Stage(
            key="stage5d_sequence_completeness_diagnostics",
            script="stage5d_sequence_completeness_diagnostics.py",
            stoppoint="crop-cache",
            build_cmd=lambda _cfg: [],
        ),
        Stage(
            key="stage5e_export_crop_cache",
            script="stage5e_export_crop_cache.py",
            stoppoint="crop-cache",
            build_cmd=lambda cfg: ["--set-num", cfg.set_num, "--bag", str(cfg.bag)],
        ),
        Stage(
            key="stage6_qty_ocr",
            script="stage6_qty_ocr.py",
            stoppoint="qty",
            build_cmd=lambda _cfg: [],
        ),
        Stage(
            key="stage7_part_segmentation",
            script="stage7_part_segmentation.py",
            stoppoint="segmentation",
            build_cmd=lambda _cfg: [],
        ),
    ]


def workspace_has_stoppoint(workspace: RunWorkspace, stoppoint: str) -> bool:
    mapping = RUN_INDEX_FILES_BY_STOPPOINT.get(stoppoint)
    if not mapping:
        return False
    required = {
        "phase1": {"page_index"},
        "step-map": {"step_map"},
        "crop-cache": {"callout_crop_box_map"},
        "qty": {"qty_ocr_map"},
        "segmentation": {"part_segmentation_map"},
    }.get(stoppoint, set(mapping.keys()))
    for key in required:
        rel = mapping.get(key)
        if not rel or not workspace.path(rel).exists():
            return False
    if stoppoint == "phase1":
        payload = _load_index(workspace.path("indexes/02_page_index.json"))
        return bool(payload and payload.get("run_id") == workspace.run_id)
    return True


def needs_pipeline_run_for_workspace(
    record: dict[str, Any] | None,
    target_stoppoint: str,
    workspace: RunWorkspace,
) -> tuple[bool, str]:
    should_run, reason = needs_pipeline_run(record, target_stoppoint)
    ws_rel = workspace.rel
    record_ws = str(record.get("run_workspace") or "") if record else ""

    if record is None:
        return True, "metadata_missing"

    if record_ws != ws_rel:
        return True, "run_workspace_missing_or_stale"

    last_completed = record.get("last_completed_stage")
    status = str(record.get("pipeline_status") or "pending")
    target_rank = stoppoint_rank(target_stoppoint)
    last_rank = stoppoint_rank(last_completed if isinstance(last_completed, str) else None)

    if status == "completed_to_stop_point" and last_rank >= target_rank:
        if workspace_has_stoppoint(workspace, target_stoppoint):
            return False, "already_completed"
        return True, "workspace_incomplete"

    if should_run:
        return should_run, reason

    if last_rank < target_rank:
        return True, "below_stop_point"

    return False, "already_completed"


def stage_already_completed(stage: Stage, record: dict[str, Any], workspace: RunWorkspace) -> bool:
    if str(record.get("run_workspace") or "") != workspace.rel:
        return False

    resume_rank = stoppoint_rank(record.get("last_completed_stage"))
    stage_rank = stoppoint_rank(stage.stoppoint)
    if stage_rank <= resume_rank and workspace_has_stoppoint(workspace, stage.stoppoint):
        return True

    if stage.key == "stage0_set_context":
        return (
            str(record.get("stage0_status") or "") == "completed"
            and workspace.path("indexes/00_set_context.json").exists()
        )
    if stage.key == "phase1_pdf_pages":
        payload = _load_index(workspace.path("indexes/02_page_index.json"))
        return (
            str(record.get("phase1_status") or "") == "completed"
            and bool(payload and payload.get("run_id") == workspace.run_id)
        )
    return False


def stages_for(config: WorkerConfig, record: dict[str, Any]) -> list[Stage]:
    target_rank = stoppoint_rank(config.stoppoint)
    selected: list[Stage] = []
    for stage in _all_stages():
        if stoppoint_rank(stage.stoppoint) > target_rank:
            continue
        if stage_already_completed(stage, record, config.workspace):
            continue
        selected.append(stage)
    return selected


def resolve_bag_from_indexes(workspace: RunWorkspace, default: int = DEFAULT_BAG) -> int:
    bag_map_path = workspace.path("indexes/04_bag_map.json")
    if not bag_map_path.exists():
        return default
    payload = json.loads(bag_map_path.read_text(encoding="utf-8"))
    bags = payload.get("bags") or []
    if not bags:
        return default
    try:
        return int(bags[0].get("bag") or default)
    except (TypeError, ValueError):
        return default


def assert_set_context_matches(set_num: str, workspace: RunWorkspace) -> None:
    context_path = workspace.path("indexes/00_set_context.json")
    if not context_path.exists():
        raise RuntimeError(f"Missing set context index: {context_path}")
    payload = json.loads(context_path.read_text(encoding="utf-8"))
    context_set = normalize_set_id(str(payload.get("set_num") or ""))
    expected = normalize_set_id(set_num)
    if context_set != expected:
        raise RuntimeError(
            f"Set context mismatch: expected catalog set {expected}, "
            f"but {workspace.rel_path(context_path)} has {context_set}. "
            f"Refusing to continue with the wrong PDF context."
        )


def assert_phase1_matches(config: WorkerConfig) -> None:
    workspace = config.workspace
    manifest_path = workspace.path("indexes/01_pdf_manifest.json")
    if not manifest_path.exists():
        raise RuntimeError(f"Missing PDF manifest after phase1: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_run_id = str(payload.get("run_id") or "")
    if manifest_run_id != config.run_id:
        raise RuntimeError(
            f"Phase1 run_id mismatch: expected {config.run_id!r}, "
            f"but {workspace.rel_path(manifest_path)} has {manifest_run_id!r}. "
            f"This usually means a stale 70618 or other hardcoded run is still in indexes/."
        )
    pdf_info = payload.get("pdf") or {}
    saved_name = Path(str(pdf_info.get("file_name") or "")).name
    expected_name = config.pdf.name
    if saved_name and saved_name != expected_name:
        raise RuntimeError(
            f"Phase1 PDF mismatch: expected {expected_name!r}, "
            f"but {workspace.rel_path(manifest_path)} references {saved_name!r}."
        )
    source_path = str(pdf_info.get("source_path") or "")
    if source_path and Path(source_path).resolve() != config.pdf.resolve():
        raise RuntimeError(
            f"Phase1 source PDF mismatch: expected {config.pdf.resolve()}, "
            f"but manifest source_path is {source_path}."
        )


def assert_safe_for_stage5(config: WorkerConfig) -> None:
    workspace = config.workspace
    context_path = workspace.path("indexes/00_set_context.json")
    step_map_path = workspace.path("indexes/05_step_map.json")
    page_index_path = workspace.path("indexes/02_page_index.json")
    pdf_manifest_path = workspace.path("indexes/01_pdf_manifest.json")

    for path in (context_path, step_map_path, page_index_path, pdf_manifest_path):
        if not path.exists():
            raise RuntimeError(f"Missing required index before Stage 5: {workspace.rel_path(path)}")

    set_context = json.loads(context_path.read_text(encoding="utf-8"))
    step_map = json.loads(step_map_path.read_text(encoding="utf-8"))
    page_index = json.loads(page_index_path.read_text(encoding="utf-8"))
    pdf_manifest = json.loads(pdf_manifest_path.read_text(encoding="utf-8"))

    expected_set = normalize_set_id(config.set_num)
    context_set = normalize_set_id(str(set_context.get("set_num") or ""))
    if context_set != expected_set:
        raise RuntimeError(
            f"Stage 5 guard failed: set context set_num={context_set!r} "
            f"does not match selected set {expected_set!r}."
        )

    manifest_run_id = str(pdf_manifest.get("run_id") or "")
    if manifest_run_id != config.run_id:
        raise RuntimeError(
            f"Stage 5 guard failed: pdf manifest run_id={manifest_run_id!r} "
            f"does not match selected run_id={config.run_id!r}."
        )

    if str(page_index.get("run_id") or "") != config.run_id:
        raise RuntimeError(
            f"Stage 5 guard failed: page index run_id={page_index.get('run_id')!r} "
            f"does not match selected run_id={config.run_id!r}."
        )

    step_map_set = normalize_set_id(str(step_map.get("set_num") or context_set))
    if step_map_set != expected_set:
        raise RuntimeError(
            f"Stage 5 guard failed: step_map set_num={step_map_set!r} "
            f"does not match set context {context_set!r}."
        )

    step_map_pages = int(step_map.get("page_count") or 0)
    page_index_count = int(page_index.get("page_count") or 0)
    if step_map_pages > page_index_count:
        raise RuntimeError(
            "Stage 5 guard failed: step_map page_count "
            f"{step_map_pages} exceeds page_index page_count {page_index_count}. "
            "Refusing to run Stage 5+ with step-map artifacts from another set."
        )


def run_stage(stage: Stage, config: WorkerConfig) -> None:
    if stage.key == "stage5_callout_crop_boxes":
        assert_safe_for_stage5(config)

    script_path = ROOT_DIR / stage.script
    if not script_path.exists():
        raise FileNotFoundError(f"Missing stage script: {script_path}")
    if stage.script in BANNED_SCRIPTS:
        raise RuntimeError(f"Refusing to run banned script: {stage.script}")

    cmd = [sys.executable, str(script_path), *stage.build_cmd(config)]
    print(f"\n==> {stage.key}: {' '.join(cmd)}", flush=True)
    print(f"    workspace: {config.workspace.rel}", flush=True)
    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True, env=config.workspace.subprocess_env())

    if stage.key == "stage0_set_context":
        assert_set_context_matches(config.set_num, config.workspace)
    elif stage.key == "phase1_pdf_pages":
        assert_phase1_matches(config)


def active_manifest_run_id(workspace: RunWorkspace) -> str | None:
    manifest_path = workspace.path("indexes/01_pdf_manifest.json")
    if not manifest_path.exists():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_id = payload.get("run_id")
    return str(run_id) if run_id else None


def _load_index(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _index_belongs_to_run(workspace: RunWorkspace) -> bool:
    return active_manifest_run_id(workspace) == workspace.run_id


def read_page_count(workspace: RunWorkspace) -> int | None:
    payload = _load_index(workspace.path("indexes/02_page_index.json"))
    if not payload or payload.get("run_id") != workspace.run_id:
        return None
    page_count = payload.get("page_count")
    return int(page_count) if page_count is not None else None


def read_bag_count(workspace: RunWorkspace) -> int | None:
    if not _index_belongs_to_run(workspace):
        return None
    payload = _load_index(workspace.path("indexes/04_bag_map.json"))
    if not payload:
        return None
    bag_count = payload.get("bag_count")
    if bag_count is not None:
        return int(bag_count)
    bags = payload.get("bags") or []
    return len(bags) if bags else None


def read_step_count(workspace: RunWorkspace) -> int | None:
    if not _index_belongs_to_run(workspace):
        return None
    payload = _load_index(workspace.path("indexes/05_step_map.json"))
    if not payload:
        return None
    step_count = payload.get("step_count")
    return int(step_count) if step_count is not None else None


def read_crop_count(workspace: RunWorkspace) -> int | None:
    if not _index_belongs_to_run(workspace):
        return None
    payload = _load_index(workspace.path("indexes/06_callout_crop_box_map.json"))
    if not payload:
        return None
    entry_count = payload.get("entry_count")
    return int(entry_count) if entry_count is not None else None


def read_ocr_count(workspace: RunWorkspace) -> int | None:
    if not _index_belongs_to_run(workspace):
        return None
    payload = _load_index(workspace.path("indexes/07_qty_ocr_map.json"))
    if not payload:
        return None
    entry_count = payload.get("entry_count")
    return int(entry_count) if entry_count is not None else None


def read_segment_count(workspace: RunWorkspace) -> int | None:
    if not _index_belongs_to_run(workspace):
        return None
    payload = _load_index(workspace.path("indexes/08_part_segmentation_map.json"))
    if not payload:
        return None
    entry_count = payload.get("entry_count")
    return int(entry_count) if entry_count is not None else None


STAGE_COUNT_READERS: dict[str, tuple[str, Callable[[RunWorkspace], int | None]]] = {
    "phase1_pdf_pages": ("page_count", read_page_count),
    "stage3_bag_map": ("bag_count", read_bag_count),
    "stage4_step_map": ("step_count", read_step_count),
    "stage5_callout_crop_boxes": ("crop_count", read_crop_count),
    "stage6_qty_ocr": ("ocr_count", read_ocr_count),
    "stage7_part_segmentation": ("segment_count", read_segment_count),
}


def counts_after_stage(stage_key: str, workspace: RunWorkspace) -> dict[str, int]:
    reader = STAGE_COUNT_READERS.get(stage_key)
    if not reader:
        return {}
    field_name, read_count = reader
    value = read_count(workspace)
    if value is None:
        return {}
    return {field_name: value}


def index_paths_after_stage(stage_key: str, workspace: RunWorkspace) -> dict[str, str]:
    mapping = STAGE_INDEX_REL_PATHS.get(stage_key)
    if not mapping:
        return {}
    outputs: dict[str, str] = {}
    for key, rel in mapping.items():
        path = workspace.path(rel)
        if path.exists():
            outputs[key] = workspace.rel_path(path)
    return outputs


def collect_index_counts(workspace: RunWorkspace, stoppoint: str) -> dict[str, int | None]:
    counts: dict[str, int | None] = {
        "page_count": read_page_count(workspace),
        "bag_count": read_bag_count(workspace),
        "step_count": read_step_count(workspace),
        "crop_count": read_crop_count(workspace),
        "ocr_count": read_ocr_count(workspace),
        "segment_count": read_segment_count(workspace),
    }
    if not _index_belongs_to_run(workspace):
        return {key: None for key in counts}

    target_rank = stoppoint_rank(stoppoint)
    if target_rank < stoppoint_rank("phase1"):
        counts["page_count"] = None
    if target_rank < stoppoint_rank("step-map"):
        counts["bag_count"] = None
        counts["step_count"] = None
    if target_rank < stoppoint_rank("crop-cache"):
        counts["crop_count"] = None
    if target_rank < stoppoint_rank("qty"):
        counts["ocr_count"] = None
    if target_rank < stoppoint_rank("segmentation"):
        counts["segment_count"] = None
    return counts


def collect_output_index_paths(workspace: RunWorkspace, stoppoint: str) -> dict[str, str]:
    if not _index_belongs_to_run(workspace):
        return {}

    outputs: dict[str, str] = {}
    target_rank = stoppoint_rank(stoppoint)
    for point, mapping in RUN_INDEX_FILES_BY_STOPPOINT.items():
        if stoppoint_rank(point) > target_rank:
            continue
        for key, rel in mapping.items():
            path = workspace.path(rel)
            if path.exists():
                outputs[key] = workspace.rel_path(path)
    return outputs


def merge_result_counts(result: dict[str, Any], counts: dict[str, int | None]) -> None:
    for key, value in counts.items():
        if value is not None:
            result[key] = value


def is_pipeline_selectable(record: dict[str, Any] | None, *, include_excluded: bool) -> bool:
    if include_excluded:
        return True
    if not record:
        return False
    return record.get("pipeline_eligible") is True


def pick_candidates(
    r2_objects: dict[str, dict[str, Any]],
    records: dict[str, dict[str, Any]],
    target_stoppoint: str,
    limit: int,
    *,
    set_num: str | None = None,
    include_excluded: bool = False,
) -> list[tuple[str, str]]:
    selected: list[tuple[str, str]] = []
    candidates = [set_num] if set_num else sorted(r2_objects.keys())
    for candidate_set in candidates:
        if candidate_set not in r2_objects:
            continue
        record = records.get(candidate_set)
        if not is_pipeline_selectable(record, include_excluded=include_excluded):
            continue
        workspace = RunWorkspace.for_set(candidate_set)
        should_run, reason = needs_pipeline_run_for_workspace(record, target_stoppoint, workspace)
        if not should_run:
            continue
        selected.append((candidate_set, reason))
        if len(selected) >= limit:
            break
    return selected


def ensure_record(
    records: dict[str, dict[str, Any]],
    set_num: str,
    r2_info: dict[str, Any],
    year: int,
) -> dict[str, Any]:
    existing = records.get(set_num)
    if existing:
        return dict(existing)
    return build_metadata_record(
        set_num=set_num,
        year=year,
        r2_key=str(r2_info.get("key") or f"pdfs/{year}/{set_num}.pdf"),
        download_status="already_in_r2",
    )


def update_record_stage(
    record: dict[str, Any],
    *,
    current_stage: str | None = None,
    stage_status_field: str | None = None,
    stage_status_value: str | None = None,
    last_completed_stage: str | None = None,
) -> dict[str, Any]:
    updated = dict(record)
    now = utc_now_iso()
    updated["updated_at"] = now
    if current_stage is not None:
        updated["current_stage"] = current_stage
    if stage_status_field and stage_status_value is not None:
        updated[stage_status_field] = stage_status_value
    if last_completed_stage is not None:
        updated["last_completed_stage"] = last_completed_stage
    return updated


def stage_status_updates(stage_key: str) -> dict[str, str]:
    updates: dict[str, str] = {}
    if stage_key == "stage0_set_context":
        updates["stage0_status"] = "completed"
    if stage_key == "phase1_pdf_pages":
        updates["phase1_status"] = "completed"
        updates["render_status"] = "completed"
    for stoppoint, last_stage in LAST_STAGE_FOR_STOPPOINT.items():
        if stage_key == last_stage:
            updates["last_completed_stage"] = stoppoint
    return updates


def process_one_pdf(
    *,
    set_num: str,
    r2_info: dict[str, Any],
    records: dict[str, dict[str, Any]],
    manifest_path: Path,
    bucket: str,
    year: int,
    stoppoint: str,
    dry_run: bool,
    client,
) -> dict[str, Any]:
    instruction_id = instruction_id_for(set_num)
    record = ensure_record(records, set_num, r2_info, year)
    workspace = RunWorkspace.for_set(set_num)
    workspace.ensure()
    r2_key = str(record.get("r2_key") or r2_info.get("key") or f"pdfs/{year}/{set_num}.pdf")
    local_pdf = local_temp_path_for(set_num)
    run_id = run_id_for(set_num)
    result: dict[str, Any] = {
        "set_num": set_num,
        "instruction_id": instruction_id,
        "run_id": run_id,
        "run_workspace": workspace.rel,
        "r2_key": r2_key,
        "local_temp_path": str(local_pdf.relative_to(ROOT_DIR)),
        "stoppoint": stoppoint,
        "resume_from": record.get("last_completed_stage"),
        "dry_run": dry_run,
        "page_count": record.get("page_count"),
        "bag_count": record.get("bag_count"),
        "step_count": record.get("step_count"),
        "crop_count": record.get("crop_count"),
        "ocr_count": record.get("ocr_count"),
        "segment_count": record.get("segment_count"),
    }

    if dry_run:
        stages = stages_for(
            WorkerConfig(
                set_num=set_num,
                pdf=local_pdf,
                run_id=run_id,
                bag=DEFAULT_BAG,
                stoppoint=stoppoint,
                workspace=workspace,
            ),
            record,
        )
        result["stages_planned"] = [stage.key for stage in stages]
        result["would_download"] = not local_pdf.exists()
        return result

    if not local_pdf.exists() or record.get("local_temp_path") != str(local_pdf.relative_to(ROOT_DIR)):
        print(f"download: {set_num} <- r2://{bucket}/{r2_key}")
        download_r2_pdf(client, bucket, r2_key, local_pdf)
        record = merge_metadata(
            record,
            {
                "local_temp_path": str(local_pdf.relative_to(ROOT_DIR)),
                "sha256": sha256_file(local_pdf),
                "file_size_bytes": local_pdf.stat().st_size,
            },
        )

    started_at = record.get("started_at") or utc_now_iso()
    record = merge_metadata(
        record,
        {
            "set_num": set_num,
            "pdf_id": instruction_id,
            "instruction_id": instruction_id,
            "r2_key": r2_key,
            "local_temp_path": str(local_pdf.relative_to(ROOT_DIR)),
            "run_id": run_id,
            "run_workspace": workspace.rel,
            "pipeline_status": "processing",
            "current_stage": "starting",
            "started_at": started_at,
            "last_error": None,
            "failed_stage": None,
            "target_stoppoint": stoppoint,
        },
    )
    records[instruction_id] = record
    save_jsonl_manifest(manifest_path, records)

    config = WorkerConfig(
        set_num=set_num,
        pdf=local_pdf.resolve(),
        run_id=run_id,
        bag=DEFAULT_BAG,
        stoppoint=stoppoint,
        workspace=workspace,
    )
    stages = stages_for(config, record)
    result["stages_planned"] = [stage.key for stage in stages]

    try:
        for stage in stages:
            if stage.key == "stage5e_export_crop_cache":
                config.bag = resolve_bag_from_indexes(workspace, DEFAULT_BAG)

            record = update_record_stage(record, current_stage=stage.key)
            records[instruction_id] = record
            save_jsonl_manifest(manifest_path, records)

            run_stage(stage, config)

            stage_updates = stage_status_updates(stage.key)
            record = merge_metadata(record, stage_updates)

            stage_counts = counts_after_stage(stage.key, workspace)
            if stage_counts:
                record = merge_metadata(record, stage_counts)
                merge_result_counts(result, stage_counts)

            stage_paths = index_paths_after_stage(stage.key, workspace)
            if stage_paths:
                output_paths = dict(record.get("output_index_paths") or {})
                output_paths.update(stage_paths)
                record["output_index_paths"] = output_paths
                result["output_index_paths"] = dict(output_paths)

            record = update_record_stage(record, current_stage=stage.key)
            records[instruction_id] = record
            save_jsonl_manifest(manifest_path, records)

        counts = collect_index_counts(workspace, stoppoint)
        outputs = collect_output_index_paths(workspace, stoppoint)
        record = merge_metadata(
            record,
            {
                "pipeline_status": "completed_to_stop_point",
                "current_stage": None,
                "last_completed_stage": stoppoint,
                "last_error": None,
                "failed_stage": None,
                "target_stoppoint": stoppoint,
                "output_index_paths": outputs or record.get("output_index_paths") or {},
                **{key: value for key, value in counts.items() if value is not None},
            },
        )
        records[instruction_id] = record
        save_jsonl_manifest(manifest_path, records)

        result.update(
            {
                "pipeline_status": "completed_to_stop_point",
                "last_completed_stage": stoppoint,
                "output_index_paths": outputs or result.get("output_index_paths") or {},
            }
        )
        merge_result_counts(result, counts)
        return result

    except Exception as exc:
        tb = traceback.format_exc()
        failed_stage = record.get("current_stage") or "unknown"
        partial_counts = collect_index_counts(workspace, stoppoint)
        record = merge_metadata(
            record,
            {
                "pipeline_status": "failed",
                "last_error": tb if isinstance(exc, subprocess.CalledProcessError) else f"{type(exc).__name__}: {exc}\n{tb}",
                "failed_stage": failed_stage,
                **{key: value for key, value in partial_counts.items() if value is not None},
            },
        )
        records[instruction_id] = record
        save_jsonl_manifest(manifest_path, records)
        result.update(
            {
                "pipeline_status": "failed",
                "failed_stage": failed_stage,
                "last_error": record["last_error"],
            }
        )
        merge_result_counts(result, partial_counts)
        raise


def load_r2_objects(*, year: int, offline: bool) -> dict[str, dict[str, Any]]:
    if offline:
        cached = load_r2_inventory_cache()
        if not cached:
            raise RuntimeError(
                f"Offline mode requires {ROOT_DIR / 'reports' / 'r2_pdf_inventory_2026.json'}"
            )
        return cached

    config = load_r2_config()
    client = create_r2_client(config)
    bucket = r2_bucket_name(config)
    return list_r2_pdfs(client, bucket, year)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Instruction V2 pipeline for one (or --limit N) 2026 PDF(s) from R2.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Stoppoints (in order):\n"
            "  phase1        stage0 + phase1 (PDF render + page index)\n"
            "  step-map      … + stage2 → stage4b\n"
            "  crop-cache    … + stage5 → stage5e\n"
            "  qty           … + stage6\n"
            "  segmentation  … + stage7\n"
        ),
    )
    parser.add_argument(
        "--to",
        choices=PIPELINE_STOPPOINTS,
        default="phase1",
        help="Run pipeline through this stoppoint (default: phase1)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Maximum number of PDFs to process (default: 1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Select candidate PDF(s) and show planned stages without downloading or running",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST_PATH),
        help=f"Metadata JSONL path (default: {DEFAULT_MANIFEST_PATH})",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=DEFAULT_YEAR,
        help=f"Instruction year (default: {DEFAULT_YEAR})",
    )
    parser.add_argument(
        "--set-num",
        default=None,
        help="Process a specific set number instead of the first eligible PDF",
    )
    parser.add_argument(
        "--include-excluded",
        action="store_true",
        help="Allow pipeline runs for records with pipeline_eligible=false",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use cached R2 inventory instead of listing R2 live",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.limit < 1:
        print("error: --limit must be >= 1", file=sys.stderr)
        return 2

    manifest_path = Path(args.manifest).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = (ROOT_DIR / manifest_path).resolve()

    records = load_jsonl_manifest(manifest_path)
    r2_objects = load_r2_objects(year=args.year, offline=args.dry_run or args.offline)
    candidates = pick_candidates(
        r2_objects,
        records,
        args.to,
        args.limit,
        set_num=args.set_num,
        include_excluded=args.include_excluded,
    )

    if not candidates:
        print(json.dumps({"ok": True, "processed": 0, "message": "No eligible PDFs found"}, indent=2))
        return 0

    client = None
    bucket = DEFAULT_R2_BUCKET
    if not args.dry_run and not args.offline:
        config = load_r2_config()
        client = create_r2_client(config)
        bucket = r2_bucket_name(config)

    results: list[dict[str, Any]] = []
    for set_num, reason in candidates:
        print(f"\nSelected: {set_num} ({reason}) -> stop={args.to}")
        try:
            result = process_one_pdf(
                set_num=set_num,
                r2_info=r2_objects[set_num],
                records=records,
                manifest_path=manifest_path,
                bucket=bucket,
                year=args.year,
                stoppoint=args.to,
                dry_run=args.dry_run,
                client=client,
            )
            results.append(result)
        except Exception:
            print(json.dumps({"ok": False, "processed": len(results), "results": results}, indent=2))
            return 1

    print(json.dumps({"ok": True, "processed": len(results), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

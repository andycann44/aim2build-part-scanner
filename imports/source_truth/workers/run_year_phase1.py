#!/usr/bin/env python3
"""Cloud/ephemeral batch Phase 1 worker for 2026 instruction PDFs.

Goal: for every eligible 2026 PDF found in R2, run Stage 0 (set context) and
Phase 1 (PDF page rendering) only, then upload the rendered pages back to R2
and persist progress metadata. This script never runs Stage 2 or any later
stage -- see BANNED_NEXT_STAGE_SCRIPTS below, enforced at the point a stage
would be invoked.

This script does not itself manage Docker. It is written so a Docker/worker
process can run it safely per-set (one PDF at a time, ephemeral local state,
no reliance on anything surviving between invocations) -- wiring it into a
container is a separate piece of work.

Default behaviour, per set:
    1. Download one PDF from R2 to local temp only.
    2. Run stage0 + phase1 (rendering happens wherever this process runs).
    3. Upload rendered pages to R2: pages/{year}/{set_num}/page_###.png
       (use --no-upload-pages-r2 to skip).
    4. Save/update progress metadata:
       set_num, year, r2_pdf_key, r2_pages_prefix, page_count,
       phase1_status, last_completed_stage, pipeline_status, updated_at.
    5. Delete the local temp PDF and run workspace before moving to the next
       set (use --keep-local to keep them).

Metadata backends (--metadata-backend azure|jsonl|both, default: both):
    - azure: write progress to Azure Table Storage, table "InstructionMetadata",
      PartitionKey=str(year), RowKey=str(set_num).
    - jsonl: write/merge progress into metadata/instruction_manifest_2026.jsonl.
    - both (default): write Azure Table + a local JSONL mirror.
    If the azure-data-tables package isn't installed, or
    AZURE_STORAGE_CONNECTION_STRING isn't set (env or .env), Azure writes are
    skipped with a warning and metadata always falls back to JSONL for that
    set, regardless of which backend was requested -- metadata is never
    silently dropped. JSONL remains useful for local debugging/recovery;
    Azure is the source of truth for automation and is preferred when
    deciding whether a set is already done (resumability).

CLI:
    python3 agents/pdf_harvester/run_year_phase1.py --year 2026 --limit 10
    python3 agents/pdf_harvester/run_year_phase1.py --year 2026 --all
    python3 agents/pdf_harvester/run_year_phase1.py --year 2026 --all --keep-local
    python3 agents/pdf_harvester/run_year_phase1.py --year 2026 --all --metadata-backend jsonl
    python3 agents/pdf_harvester/run_year_phase1.py --year 2026 --all --max-local-gb 2

Note: pipeline_status=completed_to_phase1 is a status string specific to this
script, distinct from run_one_2026_pipeline.py's completed_to_stop_point.

Safety:
    - one PDF at a time (plain sequential loop, no concurrency)
    - resumable: progress is read back (preferring Azure when available,
      falling back to local JSONL) before selecting candidates
    - every set in R2 is logged, whether selected, skipped, or processed
    - on failure: last_error is stored (JSONL only) and the run stops,
      unless --continue-on-error is passed, in which case it logs and moves
      on to the next PDF
    - never leaves rendered pages/PDF locally by default (deleted after each
      set unless --keep-local is passed)
    - aborts the whole run immediately if local temp usage exceeds
      --max-local-gb, regardless of --continue-on-error
    - skip rule: a set is considered done if phase1_status == "completed" and
      page_count is already present
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
AGENT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from harvest_pdfs import (  # noqa: E402
    DEFAULT_R2_BUCKET,
    DEFAULT_YEAR,
    _read_local_env_file,
    create_r2_client,
    load_r2_config,
    r2_bucket_name,
    sha256_file,
)
from ingest_2026 import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    list_r2_pdfs,
    load_r2_inventory_cache,
)
from instruction_metadata import (  # noqa: E402
    instruction_id_for,
    is_blank,
    load_jsonl_manifest,
    merge_metadata,
    save_jsonl_manifest,
    utc_now_iso,
)
from run_one_2026_pipeline import (  # noqa: E402
    RUNS_DIR,
    TEMP_INSTRUCTIONS_DIR,
    RunWorkspace,
    WorkerConfig,
    assert_phase1_matches,
    assert_set_context_matches,
    download_r2_pdf,
    local_temp_path_for,
    run_id_for,
)

try:
    from azure.core.exceptions import ResourceNotFoundError
    from azure.data.tables import TableServiceClient, UpdateMode

    AZURE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when package is absent
    TableServiceClient = None  # type: ignore[assignment,misc]
    UpdateMode = None  # type: ignore[assignment,misc]
    ResourceNotFoundError = Exception  # type: ignore[assignment,misc]
    AZURE_SDK_AVAILABLE = False

AZURE_TABLE_NAME = "InstructionMetadata"
AZURE_CONNECTION_STRING_ENV = "AZURE_STORAGE_CONNECTION_STRING"

# Stage 2 and everything after it. This script must never invoke any of
# these scripts -- enforced in run_stage_script() below, not just by
# omission, so a future edit can't accidentally widen scope.
BANNED_NEXT_STAGE_SCRIPTS = (
    "stage2_bag_candidates.py",
    "stage3_bag_map.py",
    "stage3b_bag_gap_review.py",
    "stage4_step_map.py",
    "stage4b_rendered_glyph_corruption_diagnostics.py",
    "stage5_callout_crop_boxes.py",
    "stage5_orchestrator.py",
    "stage5d_sequence_completeness_diagnostics.py",
    "stage5e_export_crop_cache.py",
    "stage5f_callout_quality.py",
    "stage6_qty_ocr.py",
    "stage7_part_segmentation.py",
)

ALLOWED_STAGE_SCRIPTS = ("stage0_set_context.py", "phase1_pdf_pages.py")


class LocalDiskLimitExceeded(RuntimeError):
    """Raised when local temp usage exceeds --max-local-gb. Always fatal."""


# --------------------------------------------------------------------------
# Eligibility / skip-rule helpers
# --------------------------------------------------------------------------


def is_eligible(record: dict[str, Any] | None) -> bool:
    """Eligible = has a manifest record with pipeline_eligible is True."""
    if not record:
        return False
    return record.get("pipeline_eligible") is True


def already_done(state: dict[str, Any] | None) -> bool:
    """Skip rule: phase1_status=completed and page_count exists."""
    if not state:
        return False
    return str(state.get("phase1_status") or "") == "completed" and not is_blank(
        state.get("page_count")
    )


def merged_progress_state(
    set_num: str,
    local_records: dict[str, dict[str, Any]],
    azure_progress: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Combine local JSONL + Azure progress for resumability checks.

    Azure is the source of truth for automation, so its fields win on
    overlap; JSONL fills in anything Azure doesn't track (e.g. when Azure is
    unavailable for this run).
    """
    state: dict[str, Any] = dict(local_records.get(set_num) or {})
    state.update(azure_progress.get(set_num) or {})
    return state


def classify_candidates(
    r2_objects: dict[str, dict[str, Any]],
    local_records: dict[str, dict[str, Any]],
    azure_progress: dict[str, dict[str, Any]],
) -> tuple[list[str], list[tuple[str, str]]]:
    """Split every set found in R2 into (selected, skipped-with-reason)."""
    selected: list[str] = []
    skipped: list[tuple[str, str]] = []
    for set_num in sorted(r2_objects.keys()):
        local_record = local_records.get(set_num)
        if local_record is None:
            skipped.append((set_num, "no_manifest_record_run_ingest_2026_first"))
            continue
        if not is_eligible(local_record):
            skipped.append((set_num, "pipeline_eligible_not_true"))
            continue
        state = merged_progress_state(set_num, local_records, azure_progress)
        if already_done(state):
            skipped.append((set_num, "already_completed_phase1"))
            continue
        selected.append(set_num)
    return selected, skipped


# --------------------------------------------------------------------------
# Azure Table Storage helpers (graceful degradation if unavailable)
# --------------------------------------------------------------------------


def load_azure_connection_string() -> str | None:
    env_value = str(os.environ.get(AZURE_CONNECTION_STRING_ENV) or "").strip()
    if env_value:
        return env_value
    file_value = str(_read_local_env_file().get(AZURE_CONNECTION_STRING_ENV) or "").strip()
    return file_value or None


def azure_backend_status() -> tuple[bool, str | None]:
    """Returns (usable, reason_if_not). Does not attempt a connection."""
    if not AZURE_SDK_AVAILABLE:
        return False, "azure-data-tables package is not installed"
    if not load_azure_connection_string():
        return False, f"{AZURE_CONNECTION_STRING_ENV} not set (env or .env)"
    return True, None


def get_azure_table_client() -> Any:
    conn_str = load_azure_connection_string()
    if not conn_str:
        raise RuntimeError(f"{AZURE_CONNECTION_STRING_ENV} not set (env or .env)")
    service = TableServiceClient.from_connection_string(conn_str)
    service.create_table_if_not_exists(AZURE_TABLE_NAME)
    return service.get_table_client(AZURE_TABLE_NAME)


def load_azure_progress(table_client: Any, year: int) -> dict[str, dict[str, Any]]:
    """Bulk-load every row for this year's partition into set_num -> fields."""
    progress: dict[str, dict[str, Any]] = {}
    if table_client is None:
        return progress
    query_filter = f"PartitionKey eq '{year}'"
    for entity in table_client.query_entities(query_filter=query_filter):
        set_num = str(entity.get("RowKey") or "")
        if set_num:
            progress[set_num] = dict(entity)
    return progress


def write_azure_entity(
    table_client: Any, *, year: int, set_num: str, fields: dict[str, Any]
) -> None:
    entity: dict[str, Any] = {"PartitionKey": str(year), "RowKey": str(set_num)}
    for key, value in fields.items():
        if value is not None:
            entity[key] = value
    table_client.upsert_entity(entity, mode=UpdateMode.MERGE)


def verify_azure_row(spec: str) -> int:
    """Read-only lookup of exactly one row in Azure Table Storage.

    Never calls create_table_if_not_exists, never upserts, never touches R2,
    local JSONL, or the filesystem. Parses spec as 'YEAR:SET_NUM', prints a
    JSON result, and returns a process exit code.
    """
    if ":" not in spec:
        print(f"error: --verify-azure-row must be YEAR:SET_NUM, got {spec!r}", file=sys.stderr)
        return 2
    year_str, set_num = spec.split(":", 1)
    year_str = year_str.strip()
    set_num = set_num.strip()
    if not year_str or not set_num:
        print(f"error: --verify-azure-row must be YEAR:SET_NUM, got {spec!r}", file=sys.stderr)
        return 2

    usable, reason = azure_backend_status()
    if not usable:
        print(f"ERROR: Azure Table Storage unavailable ({reason}); cannot verify.", file=sys.stderr)
        return 1

    try:
        from azure.core.exceptions import ResourceNotFoundError

        conn_str = load_azure_connection_string()
        service = TableServiceClient.from_connection_string(conn_str)
        # Deliberately use get_table_client() directly here, NOT
        # get_azure_table_client(), because that helper calls
        # create_table_if_not_exists() -- a write. This lookup must be
        # strictly read-only, so a missing table is just reported as
        # "not found" rather than created.
        table_client = service.get_table_client(AZURE_TABLE_NAME)
        entity = table_client.get_entity(partition_key=year_str, row_key=set_num)
    except ResourceNotFoundError:
        print(
            json.dumps(
                {
                    "found": False,
                    "table": AZURE_TABLE_NAME,
                    "partition_key": year_str,
                    "row_key": set_num,
                },
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        print(f"ERROR: could not connect to Azure Table Storage ({exc})", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "found": True,
                "table": AZURE_TABLE_NAME,
                "partition_key": year_str,
                "row_key": set_num,
                "page_count": entity.get("page_count"),
                "phase1_status": entity.get("phase1_status"),
                "pipeline_status": entity.get("pipeline_status"),
                "updated_at": entity.get("updated_at"),
                "r2_pages_prefix": entity.get("r2_pages_prefix"),
            },
            indent=2,
        )
    )
    return 0


def persist_progress(
    *,
    set_num: str,
    year: int,
    azure_table_client: Any,
    metadata_backend: str,
    azure_fields: dict[str, Any],
    jsonl_fields: dict[str, Any],
    local_records: dict[str, dict[str, Any]],
    manifest_path: Path,
) -> None:
    """Write progress to the requested backend(s), with JSONL as a safety
    net whenever Azure was requested but unavailable/failing -- metadata is
    never silently dropped."""
    azure_requested = metadata_backend in ("azure", "both")
    jsonl_requested = metadata_backend in ("jsonl", "both")

    azure_ok = False
    if azure_requested:
        if azure_table_client is not None:
            try:
                write_azure_entity(azure_table_client, year=year, set_num=set_num, fields=azure_fields)
                azure_ok = True
            except Exception as exc:
                print(
                    f"  WARNING: Azure Table write failed for {set_num} ({exc}); "
                    "falling back to JSONL",
                    file=sys.stderr,
                    flush=True,
                )
        else:
            print(
                f"  WARNING: Azure Table Storage unavailable; writing JSONL only for {set_num}",
                file=sys.stderr,
                flush=True,
            )

    if jsonl_requested or (azure_requested and not azure_ok):
        instruction_id = instruction_id_for(set_num)
        record = dict(local_records.get(set_num) or {})
        record = merge_metadata(record, jsonl_fields)
        # merge_metadata skips blank incoming values, so clear these
        # explicitly when the caller intends to (e.g. clearing a previous
        # failure on success).
        for clear_key in ("last_error", "failed_stage"):
            if clear_key in jsonl_fields:
                record[clear_key] = jsonl_fields[clear_key]
        local_records[instruction_id] = record
        save_jsonl_manifest(manifest_path, local_records)


# --------------------------------------------------------------------------
# Local disk cap + cleanup
# --------------------------------------------------------------------------


def local_dir_size_bytes(*paths: Path) -> int:
    total = 0
    for path in paths:
        if not path.exists():
            continue
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    continue
    return total


def enforce_local_disk_cap(max_local_gb: float | None) -> None:
    if max_local_gb is None:
        return
    used_bytes = local_dir_size_bytes(TEMP_INSTRUCTIONS_DIR, RUNS_DIR)
    cap_bytes = max_local_gb * (1024**3)
    if used_bytes > cap_bytes:
        used_gb = used_bytes / (1024**3)
        raise LocalDiskLimitExceeded(
            f"local temp usage {used_gb:.2f} GB exceeds --max-local-gb {max_local_gb} GB "
            f"(checked {TEMP_INSTRUCTIONS_DIR} and {RUNS_DIR})"
        )


def cleanup_local_artifacts(local_pdf: Path, workspace: RunWorkspace) -> None:
    pdf_dir = local_pdf.parent
    if pdf_dir.exists():
        shutil.rmtree(pdf_dir, ignore_errors=True)
    if workspace.root.exists():
        shutil.rmtree(workspace.root, ignore_errors=True)


# --------------------------------------------------------------------------
# R2 page upload
# --------------------------------------------------------------------------


def upload_pages_to_r2(
    client: Any, *, bucket: str, year: int, set_num: str, pages_dir: Path
) -> tuple[str, int]:
    """Upload every rendered page in pages_dir to pages/{year}/{set_num}/.

    Existing filenames (page_001.png, page_002.png, ...) already match the
    repo-wide zero-padded convention, so they're reused as-is -- no rename.
    """
    prefix = f"pages/{year}/{set_num}/"
    page_files = sorted(pages_dir.glob("page_*.png"))
    if not page_files:
        raise RuntimeError(f"no rendered pages found in {pages_dir} to upload")
    for page_file in page_files:
        key = f"{prefix}{page_file.name}"
        client.upload_file(str(page_file), bucket, key)
    return prefix, len(page_files)


# --------------------------------------------------------------------------
# Stage execution
# --------------------------------------------------------------------------


def run_stage_script(
    script_name: str, args: list[str], workspace: RunWorkspace
) -> subprocess.CompletedProcess:
    if script_name not in ALLOWED_STAGE_SCRIPTS or script_name in BANNED_NEXT_STAGE_SCRIPTS:
        raise RuntimeError(f"Refusing to run non-phase1 stage script: {script_name}")
    script_path = ROOT_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Missing stage script: {script_path}")
    cmd = [sys.executable, str(script_path), *args]
    print(f"    -> {' '.join(cmd)}", flush=True)
    return subprocess.run(
        cmd,
        cwd=str(ROOT_DIR),
        check=True,
        capture_output=True,
        text=True,
        env=workspace.subprocess_env(),
    )


def process_one_pdf(
    *,
    set_num: str,
    r2_info: dict[str, Any],
    local_records: dict[str, dict[str, Any]],
    manifest_path: Path,
    bucket: str,
    year: int,
    client: Any,
    azure_table_client: Any,
    metadata_backend: str,
    upload_pages: bool,
    keep_local: bool,
    max_local_gb: float | None,
) -> dict[str, Any]:
    instruction_id = instruction_id_for(set_num)
    record = dict(local_records.get(set_num) or {})
    workspace = RunWorkspace.for_set(set_num)
    workspace.ensure()
    r2_key = str(record.get("r2_key") or r2_info.get("key") or f"pdfs/{year}/{set_num}.pdf")
    local_pdf = local_temp_path_for(set_num)
    run_id = run_id_for(set_num)

    print(f"\n=== {set_num} ===", flush=True)

    enforce_local_disk_cap(max_local_gb)

    if not local_pdf.exists():
        print(f"  download: r2://{bucket}/{r2_key} -> {local_pdf}", flush=True)
        download_r2_pdf(client, bucket, r2_key, local_pdf)
    else:
        print(f"  pdf already on disk: {local_pdf}", flush=True)

    enforce_local_disk_cap(max_local_gb)

    print("  run stage0_set_context", flush=True)
    run_stage_script("stage0_set_context.py", ["--set-num", set_num], workspace)
    assert_set_context_matches(set_num, workspace)

    print("  run phase1_pdf_pages", flush=True)
    phase1_proc = run_stage_script(
        "phase1_pdf_pages.py",
        ["--pdf", str(local_pdf.resolve()), "--run-id", run_id],
        workspace,
    )
    config = WorkerConfig(
        set_num=set_num,
        pdf=local_pdf.resolve(),
        run_id=run_id,
        bag=1,
        stoppoint="phase1",
        workspace=workspace,
    )
    assert_phase1_matches(config)
    phase1_result = json.loads(phase1_proc.stdout)

    enforce_local_disk_cap(max_local_gb)

    page_count = phase1_result.get("page_count")
    pages_dir_rel = phase1_result.get("pages_dir")
    pages_dir_abs = (ROOT_DIR / pages_dir_rel) if pages_dir_rel else None
    pdf_sha256 = sha256_file(local_pdf)

    r2_pages_prefix = None
    if upload_pages:
        if not pages_dir_abs or not pages_dir_abs.exists():
            raise RuntimeError(f"rendered pages directory not found: {pages_dir_abs}")
        print(f"  upload pages -> r2://{bucket}/pages/{year}/{set_num}/", flush=True)
        r2_pages_prefix, uploaded_count = upload_pages_to_r2(
            client, bucket=bucket, year=year, set_num=set_num, pages_dir=pages_dir_abs
        )
        print(f"  uploaded {uploaded_count} page(s) to r2://{bucket}/{r2_pages_prefix}", flush=True)
    else:
        print("  --no-upload-pages-r2: skipping page upload", flush=True)

    now = utc_now_iso()
    azure_fields = {
        "set_num": set_num,
        "year": year,
        "r2_pdf_key": r2_key,
        "r2_pages_prefix": r2_pages_prefix,
        "page_count": page_count,
        "phase1_status": "completed",
        "last_completed_stage": "phase1",
        "pipeline_status": "completed_to_phase1",
        "updated_at": now,
    }
    jsonl_fields = {
        **azure_fields,
        "instruction_id": instruction_id,
        "pdf_id": instruction_id,
        "run_id": phase1_result.get("run_id") or run_id,
        "pdf_sha256": pdf_sha256,
        "last_error": None,
        "failed_stage": None,
    }

    persist_progress(
        set_num=set_num,
        year=year,
        azure_table_client=azure_table_client,
        metadata_backend=metadata_backend,
        azure_fields=azure_fields,
        jsonl_fields=jsonl_fields,
        local_records=local_records,
        manifest_path=manifest_path,
    )

    if not keep_local:
        print("  cleanup: removing local temp PDF and run workspace", flush=True)
        cleanup_local_artifacts(local_pdf, workspace)
    else:
        print("  --keep-local: leaving local temp PDF/pages/workspace on disk", flush=True)

    print(
        f"  done: page_count={page_count} pages_uploaded={'yes' if upload_pages else 'no'}",
        flush=True,
    )
    return jsonl_fields


# --------------------------------------------------------------------------
# R2 listing
# --------------------------------------------------------------------------


def load_r2_objects_for_year(year: int) -> tuple[dict[str, dict[str, Any]], Any, str]:
    """Returns (r2_objects, client_or_None, bucket). Falls back to the local
    inventory cache (with no client) if live R2 listing is unavailable."""
    try:
        config = load_r2_config()
        bucket = r2_bucket_name(config)
        client = create_r2_client(config)
        print(f"listing R2 bucket={bucket} prefix=pdfs/{year}/", flush=True)
        r2_objects = list_r2_pdfs(client, bucket, year)
        return r2_objects, client, bucket
    except Exception as exc:
        print(
            f"R2 listing unavailable ({exc}); falling back to local inventory cache "
            "(downloads of new PDFs and page uploads will fail until R2 credentials "
            "are available)",
            file=sys.stderr,
            flush=True,
        )
        cached = {
            key: value
            for key, value in load_r2_inventory_cache().items()
            if str(value.get("key", "")).startswith(f"pdfs/{year}/")
        }
        return cached, None, DEFAULT_R2_BUCKET


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Cloud/ephemeral batch Phase 1 worker: stage0 + phase1 only, for every "
            "eligible 2026 PDF in R2. Downloads to temp, uploads rendered pages to "
            "R2, persists progress metadata, then deletes local state by default. "
            "Never runs Stage 2 or later."
        ),
    )
    parser.add_argument(
        "--year",
        type=int,
        default=DEFAULT_YEAR,
        help=f"Instruction year (default: {DEFAULT_YEAR})",
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--limit", type=int, help="Process at most N eligible PDFs.")
    group.add_argument(
        "--all", action="store_true", help="Process every eligible PDF found (no limit)."
    )
    group.add_argument(
        "--set-num",
        type=str,
        help=(
            "Process exactly this one set_num, bypassing eligibility/already-done "
            "candidate selection. For manual verification/debugging of a single set."
        ),
    )
    parser.add_argument(
        "--verify-azure-row",
        type=str,
        metavar="YEAR:SET_NUM",
        help=(
            "Read-only mode: look up one row in Azure Table Storage "
            "(table %r, PartitionKey=YEAR, RowKey=SET_NUM) and print its "
            "progress fields, then exit. Does not touch R2, does not download "
            "or render anything, does not write to Azure or JSONL. "
            "Example: --verify-azure-row 2026:11384-1" % AZURE_TABLE_NAME
        ),
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help=(
            "On failure for one PDF, store last_error and continue to the next PDF "
            "instead of stopping the run. Does not apply to --max-local-gb breaches, "
            "which always stop the run."
        ),
    )
    parser.add_argument(
        "--keep-local",
        action="store_true",
        help=(
            "Do not delete the local temp PDF, rendered pages, or run workspace "
            "after each set (default: delete after each set)."
        ),
    )
    parser.add_argument(
        "--upload-pages-r2",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Upload rendered pages to R2 at pages/{year}/{set_num}/page_###.png "
            "(default: on; pass --no-upload-pages-r2 to skip)."
        ),
    )
    parser.add_argument(
        "--metadata-backend",
        choices=("azure", "jsonl", "both"),
        default="both",
        help=(
            "Where to persist phase1 progress metadata (default: both -- Azure "
            "Table Storage plus a local JSONL mirror; falls back to JSONL-only "
            "with a warning if Azure is unavailable)."
        ),
    )
    parser.add_argument(
        "--max-local-gb",
        type=float,
        default=5.0,
        help=(
            "Abort the run if local temp usage (downloaded PDFs + run workspaces "
            "under temp/instructions/ and runs/) exceeds this many GB (default: 5)."
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.verify_azure_row:
        # Read-only verification mode: no R2, no download, no render, no
        # metadata writes. Exit immediately, before any other setup below.
        return verify_azure_row(args.verify_azure_row)

    if args.limit is None and not args.all and not args.set_num:
        print(
            "error: one of --limit, --all, --set-num, or --verify-azure-row is required",
            file=sys.stderr,
        )
        return 2
    if args.limit is not None and args.limit < 1:
        print("error: --limit must be >= 1", file=sys.stderr)
        return 2
    if args.max_local_gb is not None and args.max_local_gb <= 0:
        print("error: --max-local-gb must be > 0", file=sys.stderr)
        return 2

    manifest_path = DEFAULT_MANIFEST_PATH
    local_records = load_jsonl_manifest(manifest_path)
    r2_objects, client, bucket = load_r2_objects_for_year(args.year)

    azure_table_client = None
    if args.metadata_backend in ("azure", "both"):
        usable, reason = azure_backend_status()
        if not usable:
            print(
                f"WARNING: Azure Table Storage unavailable ({reason}); metadata will "
                "be written to local JSONL only.",
                file=sys.stderr,
                flush=True,
            )
        else:
            try:
                azure_table_client = get_azure_table_client()
            except Exception as exc:
                print(
                    f"WARNING: could not connect to Azure Table Storage ({exc}); "
                    "metadata will be written to local JSONL only.",
                    file=sys.stderr,
                    flush=True,
                )

    azure_progress = load_azure_progress(azure_table_client, args.year)

    if args.set_num:
        selected = [args.set_num]
        skipped: list[tuple[str, str]] = []
        if args.set_num not in r2_objects:
            r2_objects = dict(r2_objects)
            r2_objects[args.set_num] = {}
        print(f"--set-num override: processing exactly {args.set_num} (skip rule bypassed)", flush=True)
    else:
        selected, skipped = classify_candidates(r2_objects, local_records, azure_progress)
        for set_num, reason in skipped:
            print(f"skip {set_num}: {reason}", flush=True)

        if not args.all and args.limit is not None:
            selected = selected[: args.limit]

    if not selected:
        print(json.dumps({"ok": True, "processed": 0, "message": "No eligible PDFs found"}, indent=2))
        return 0

    print(f"\nselected {len(selected)} set(s): {', '.join(selected)}", flush=True)

    processed = 0
    failed = 0
    for index, set_num in enumerate(selected, start=1):
        print(f"\n[{index}/{len(selected)}] set {set_num}", flush=True)
        try:
            process_one_pdf(
                set_num=set_num,
                r2_info=r2_objects[set_num],
                local_records=local_records,
                manifest_path=manifest_path,
                bucket=bucket,
                year=args.year,
                client=client,
                azure_table_client=azure_table_client,
                metadata_backend=args.metadata_backend,
                upload_pages=args.upload_pages_r2,
                keep_local=args.keep_local,
                max_local_gb=args.max_local_gb,
            )
            processed += 1
        except LocalDiskLimitExceeded as exc:
            print(f"\nABORTING RUN: {exc}", file=sys.stderr, flush=True)
            failed += 1
            break
        except Exception as exc:
            failed += 1
            if isinstance(exc, subprocess.CalledProcessError):
                error_text = (
                    f"CalledProcessError: cmd={exc.cmd} returncode={exc.returncode}\n"
                    f"stdout={exc.stdout}\nstderr={exc.stderr}"
                )
            else:
                error_text = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            print(f"  FAILED: {set_num}: {exc}", file=sys.stderr, flush=True)

            now = utc_now_iso()
            persist_progress(
                set_num=set_num,
                year=args.year,
                azure_table_client=azure_table_client,
                metadata_backend=args.metadata_backend,
                azure_fields={
                    "set_num": set_num,
                    "year": args.year,
                    "pipeline_status": "failed",
                    "updated_at": now,
                },
                jsonl_fields={
                    "set_num": set_num,
                    "instruction_id": instruction_id_for(set_num),
                    "last_error": error_text,
                    "failed_stage": "phase1",
                    "pipeline_status": "failed",
                    "updated_at": now,
                },
                local_records=local_records,
                manifest_path=manifest_path,
            )

            if not args.continue_on_error:
                print(
                    f"\nStopping after failure on {set_num} "
                    "(pass --continue-on-error to keep going).",
                    file=sys.stderr,
                    flush=True,
                )
                break

    summary = {
        "ok": failed == 0,
        "processed": processed,
        "failed": failed,
        "skipped": len(skipped),
        "total_selected": len(selected),
    }
    print(json.dumps(summary, indent=2))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

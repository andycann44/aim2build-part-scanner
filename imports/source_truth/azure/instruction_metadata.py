"""Instruction PDF metadata records for the 2026 ingestion pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def instruction_id_for(set_num: str) -> str:
    return str(set_num)


def pdf_filename_for(set_num: str) -> str:
    return f"{set_num}.pdf"


def r2_object_ref(bucket: str, r2_key: str) -> str:
    return f"r2://{bucket}/{r2_key}"


def r2_public_url(public_base: str | None, r2_key: str) -> str | None:
    if not public_base:
        return None
    base = public_base.rstrip("/")
    return f"{base}/{r2_key.lstrip('/')}"


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, dict)) and not value:
        return True
    return False


def merge_metadata(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge records without overwriting good values with blank/null."""
    merged = dict(existing)
    for key, value in incoming.items():
        if is_blank(value):
            continue
        merged[key] = value
    now = utc_now_iso()
    merged["updated_at"] = now
    if is_blank(merged.get("created_at")):
        merged["created_at"] = now
    return merged


def compute_ready_flags(record: dict[str, Any]) -> dict[str, bool]:
    in_r2 = str(record.get("download_status") or "") in {
        "already_in_r2",
        "uploaded_r2",
        "downloaded",
    }
    has_source = not is_blank(record.get("source_url"))
    has_key = not is_blank(record.get("r2_key"))
    has_error = not is_blank(record.get("last_error"))
    unresolved = str(record.get("download_status") or "") in {"failed", "unresolved"}

    ready_for_phase1 = in_r2 and has_source and has_key
    ready_for_stage0 = ready_for_phase1
    pipeline_eligible = record.get("pipeline_eligible")
    if pipeline_eligible is None:
        pipeline_eligible = True
    ready_for_pipeline = bool(pipeline_eligible) and ready_for_phase1
    needs_review = has_error or unresolved

    return {
        "metadata_created": True,
        "ready_for_phase1": ready_for_phase1,
        "ready_for_stage0": ready_for_stage0,
        "ready_for_pipeline": ready_for_pipeline,
        "needs_review": needs_review,
    }


def build_metadata_record(
    *,
    set_num: str,
    year: int,
    title: str | None = None,
    theme: str | None = None,
    source_url: str | None = None,
    r2_key: str | None = None,
    r2_url: str | None = None,
    r2_object_ref_value: str | None = None,
    local_temp_path: str | None = None,
    download_status: str,
    downloaded_at: str | None = None,
    page_count: int | None = None,
    file_size_bytes: int | None = None,
    sha256: str | None = None,
    render_status: str = "pending",
    stage0_status: str = "pending",
    phase1_status: str = "pending",
    pipeline_status: str = "pending",
    last_error: str | None = None,
    created_at: str | None = None,
    updated_at: str | None = None,
) -> dict[str, Any]:
    instruction_id = instruction_id_for(set_num)
    now = utc_now_iso()
    record: dict[str, Any] = {
        "set_num": set_num,
        "instruction_id": instruction_id,
        "pdf_id": instruction_id,
        "year": year,
        "theme": theme,
        "title": title,
        "pdf_filename": pdf_filename_for(set_num),
        "r2_key": r2_key,
        "r2_url": r2_url,
        "r2_object_ref": r2_object_ref_value,
        "local_temp_path": local_temp_path,
        "source_url": source_url,
        "download_status": download_status,
        "downloaded_at": downloaded_at,
        "page_count": page_count,
        "file_size_bytes": file_size_bytes,
        "sha256": sha256,
        "render_status": render_status,
        "stage0_status": stage0_status,
        "phase1_status": phase1_status,
        "pipeline_status": pipeline_status,
        "last_error": last_error,
        "created_at": created_at or now,
        "updated_at": updated_at or now,
    }
    record.update(compute_ready_flags(record))
    return record


def load_jsonl_manifest(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        key = str(payload.get("instruction_id") or payload.get("set_num") or "")
        if key:
            records[key] = payload
    return records


PIPELINE_STOPPOINTS = (
    "phase1",
    "step-map",
    "crop-cache",
    "qty",
    "segmentation",
)

STOPPOINT_RANK = {name: index for index, name in enumerate(PIPELINE_STOPPOINTS)}


def stoppoint_rank(name: str | None) -> int:
    if not name:
        return -1
    return STOPPOINT_RANK.get(str(name), -1)


def needs_pipeline_run(
    record: dict[str, Any] | None,
    target_stoppoint: str,
) -> tuple[bool, str]:
    """Return whether a PDF should be processed and why."""
    if record is None:
        return True, "metadata_missing"

    target_rank = stoppoint_rank(target_stoppoint)
    last_completed = record.get("last_completed_stage")
    last_rank = stoppoint_rank(last_completed if isinstance(last_completed, str) else None)
    status = str(record.get("pipeline_status") or "pending")

    if status in {"processing", "failed"}:
        return True, f"resume_{status}"

    if status == "completed_to_stop_point" and last_rank >= target_rank:
        return False, "already_completed"

    if last_rank < target_rank:
        return True, "below_stop_point"

    if status != "completed_to_stop_point":
        return True, "incomplete"

    return False, "already_completed"


def save_jsonl_manifest(path: Path, records: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(record, ensure_ascii=True, sort_keys=True)
        for _, record in sorted(records.items(), key=lambda item: item[0])
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def legacy_manifest_to_records(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    year = int(manifest.get("year") or 2026)
    bucket = str(manifest.get("r2_bucket") or "aim2build-instructions")
    for entry in manifest.get("entries") or []:
        set_num = str(entry.get("set_num") or "")
        if not set_num:
            continue
        r2_key = str(entry.get("r2_key") or entry.get("r2_key_future") or f"pdfs/{year}/{set_num}.pdf")
        download_status = str(entry.get("status") or "")
        if download_status == "uploaded_r2":
            download_status = "already_in_r2"
        elif download_status == "skipped_exists":
            download_status = "already_in_r2"
        record = build_metadata_record(
            set_num=set_num,
            year=year,
            title=entry.get("name"),
            source_url=entry.get("pdf_url"),
            r2_key=r2_key,
            r2_object_ref_value=r2_object_ref(bucket, r2_key),
            local_temp_path=entry.get("local_path"),
            download_status=download_status or "unknown",
            downloaded_at=entry.get("downloaded_at") or entry.get("r2_uploaded_at"),
            file_size_bytes=entry.get("file_size_bytes"),
            sha256=entry.get("sha256"),
            created_at=entry.get("downloaded_at"),
            updated_at=entry.get("r2_uploaded_at") or entry.get("downloaded_at"),
        )
        records[instruction_id_for(set_num)] = record
    return records

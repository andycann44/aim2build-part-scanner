#!/usr/bin/env python3
"""Year-scoped LEGO instruction PDF harvester — metadata + PDF collection only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
AGENT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from paths import INDEXES_DIR, PDFS_DIR  # noqa: E402

from lego_reader.downloader import (  # noqa: E402
    DownloadError,
    SetNotFoundError,
    download_set_pdfs,
    resolve_set_pdf_links,
)
from lego_reader.utils import normalize_set_num  # noqa: E402

DEFAULT_YEAR = 2026
DEFAULT_SEED_PATH = AGENT_DIR / "seeds_2026.json"
DEFAULT_R2_BUCKET = "aim2build-instructions"
R2_REQUIRED_KEYS = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
R2_OPTIONAL_KEYS = ("R2_PUBLIC_BASE_URL", "R2_BUCKET")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def r2_key_for(set_num: str, year: int) -> str:
    return f"pdfs/{year}/{set_num}.pdf"


def local_pdf_path(set_num: str, year: int) -> Path:
    return PDFS_DIR / str(year) / f"{set_num}.pdf"


def relative_local_path(set_num: str, year: int) -> str:
    return r2_key_for(set_num, year)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_seeds(seeds_path: Path) -> tuple[int, list[dict[str, Any]]]:
    payload = json.loads(seeds_path.read_text(encoding="utf-8"))
    seeds = payload.get("seeds", [])
    if not isinstance(seeds, list):
        raise ValueError(f"Expected 'seeds' list in {seeds_path}")
    year = int(payload.get("year") or DEFAULT_YEAR)
    return year, seeds


def load_manifest(manifest_path: Path, *, year: int) -> dict[str, Any]:
    if not manifest_path.exists():
        return {
            "agent": "pdf_harvester",
            "year": year,
            "updated_at_utc": None,
            "entries": [],
        }
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def save_manifest(manifest_path: Path, payload: dict[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def upsert_manifest_entry(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    entries = manifest.setdefault("entries", [])
    set_num = entry["set_num"]
    for index, existing in enumerate(entries):
        if existing.get("set_num") == set_num:
            entries[index] = entry
            return
    entries.append(entry)


def build_entry(
    *,
    set_num: str,
    name: str,
    year: int,
    pdf_url: str | None,
    status: str,
    local_path: str | None = None,
    file_size_bytes: int | None = None,
    sha256: str | None = None,
    downloaded_at: str | None = None,
    r2_key: str | None = None,
    r2_uploaded_at: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    entry = {
        "set_num": set_num,
        "name": name,
        "year": year,
        "pdf_url": pdf_url,
        "r2_key_future": r2_key_for(set_num, year),
        "local_path": local_path,
        "file_size_bytes": file_size_bytes,
        "sha256": sha256,
        "status": status,
        "downloaded_at": downloaded_at,
    }
    if r2_key:
        entry["r2_key"] = r2_key
    if r2_uploaded_at:
        entry["r2_uploaded_at"] = r2_uploaded_at
    if source:
        entry["source"] = source
    return entry


def _read_local_env_file() -> dict[str, str]:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists() or not env_path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def load_r2_config() -> dict[str, str]:
    local_env = _read_local_env_file()
    values: dict[str, str] = {}
    for key in R2_REQUIRED_KEYS + R2_OPTIONAL_KEYS:
        env_value = str(os.environ.get(key) or "").strip()
        if env_value:
            values[key] = env_value
            continue
        file_value = str(local_env.get(key) or "").strip()
        if file_value:
            values[key] = file_value
    missing = [key for key in R2_REQUIRED_KEYS if not values.get(key)]
    if missing:
        raise RuntimeError(f"Missing R2 config: {', '.join(missing)}")
    if not values.get("R2_BUCKET"):
        values["R2_BUCKET"] = DEFAULT_R2_BUCKET
    return values


def r2_bucket_name(config: dict[str, str]) -> str:
    return str(config.get("R2_BUCKET") or DEFAULT_R2_BUCKET)


def create_r2_client(config: dict[str, str]):
    try:
        import boto3  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("boto3 is required for R2 upload") from exc

    endpoint_url = f"https://{config['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=config["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=config["R2_SECRET_ACCESS_KEY"],
    )


def upload_pdf_to_r2(
    client,
    *,
    local_path: Path,
    bucket: str,
    r2_key: str,
) -> None:
    client.upload_file(str(local_path), bucket, r2_key)


def manifest_r2_key(year: int) -> str:
    return f"manifests/{year}/pdf_manifest_{year}.json"


def upload_manifest_to_r2(
    client,
    *,
    manifest_path: Path,
    bucket: str,
    r2_key: str,
) -> None:
    client.upload_file(str(manifest_path), bucket, r2_key)


def download_pdf_url(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "aim2build-pdf-harvester/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def resolve_pdf_url(seed: dict[str, Any]) -> str:
    explicit = seed.get("pdf_url")
    if explicit:
        return str(explicit)

    lookup_num = normalize_set_num(str(seed["set_num"]))
    _, _, entries = resolve_set_pdf_links(lookup_num)
    return entries[0][1]


def download_seed_pdf(seed: dict[str, Any], target: Path) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    if seed.get("pdf_url"):
        pdf_url = str(seed["pdf_url"])
        download_pdf_url(pdf_url, target)
        return pdf_url

    lookup_num = normalize_set_num(str(seed["set_num"]))
    with tempfile.TemporaryDirectory(prefix="pdf_harvest_") as temp_dir:
        download_result = download_set_pdfs(
            set_num=lookup_num,
            instructions_dir=Path(temp_dir),
        )
        if not download_result.pdfs:
            raise DownloadError(f"No PDFs returned for set {lookup_num}")
        downloaded = download_result.pdfs[0]
        shutil.copy2(downloaded.local_path, target)
        return downloaded.source_url


def plan_seed(
    seed: dict[str, Any],
    *,
    year: int,
    upload_r2: bool = False,
) -> dict[str, Any]:
    set_num = str(seed["set_num"])
    name = str(seed.get("name") or "")
    source = str(seed.get("source") or "seed")
    rel_path = relative_local_path(set_num, year)
    r2_key = r2_key_for(set_num, year)
    target = local_pdf_path(set_num, year)

    if not upload_r2 and target.exists():
        return build_entry(
            set_num=set_num,
            name=name,
            year=year,
            pdf_url=seed.get("pdf_url"),
            status="skipped_exists",
            local_path=rel_path,
            file_size_bytes=target.stat().st_size,
            sha256=sha256_file(target),
            downloaded_at=None,
            source=source,
        )

    try:
        pdf_url = resolve_pdf_url(seed)
    except (DownloadError, SetNotFoundError, ValueError) as exc:
        return build_entry(
            set_num=set_num,
            name=name,
            year=year,
            pdf_url=seed.get("pdf_url"),
            status="unresolved",
            local_path=rel_path,
            file_size_bytes=None,
            sha256=None,
            downloaded_at=None,
            source=source,
        )

    return build_entry(
        set_num=set_num,
        name=name,
        year=year,
        pdf_url=pdf_url,
        status="planned_r2" if upload_r2 else "planned",
        local_path=r2_key if upload_r2 else rel_path,
        file_size_bytes=None,
        sha256=None,
        downloaded_at=None,
        r2_key=r2_key if upload_r2 else None,
        source=source,
    )


def harvest_seed(
    seed: dict[str, Any],
    *,
    year: int,
    upload_r2: bool = False,
    delete_local_after_upload: bool = False,
    r2_client=None,
    r2_bucket: str = DEFAULT_R2_BUCKET,
) -> dict[str, Any]:
    set_num = str(seed["set_num"])
    name = str(seed.get("name") or "")
    source = str(seed.get("source") or "seed")
    rel_path = relative_local_path(set_num, year)
    r2_key = r2_key_for(set_num, year)
    target = local_pdf_path(set_num, year)

    if not upload_r2 and target.exists():
        print(f"skip existing: {set_num} -> {rel_path}")
        existing_url = seed.get("pdf_url")
        return build_entry(
            set_num=set_num,
            name=name,
            year=year,
            pdf_url=str(existing_url) if existing_url else None,
            status="skipped_exists",
            local_path=rel_path,
            file_size_bytes=target.stat().st_size,
            sha256=sha256_file(target),
            downloaded_at=None,
            source=source,
        )

    try:
        with tempfile.TemporaryDirectory(prefix="pdf_harvest_") as temp_dir:
            temp_path = Path(temp_dir) / f"{set_num}.pdf"
            source_label = seed.get("pdf_url") or "lego.com building instructions"
            print(f"download: {set_num} <- {source_label}")
            pdf_url = download_seed_pdf(seed, temp_path)
            file_size_bytes = temp_path.stat().st_size
            digest = sha256_file(temp_path)
            downloaded_at = utc_now_iso()

            if upload_r2:
                if r2_client is None:
                    raise RuntimeError("R2 client is required for upload mode")
                print(f"upload: {set_num} -> r2://{r2_bucket}/{r2_key}")
                upload_pdf_to_r2(
                    r2_client,
                    local_path=temp_path,
                    bucket=r2_bucket,
                    r2_key=r2_key,
                )
                if delete_local_after_upload and temp_path.exists():
                    temp_path.unlink()
                return build_entry(
                    set_num=set_num,
                    name=name,
                    year=year,
                    pdf_url=pdf_url,
                    status="uploaded_r2",
                    local_path=r2_key,
                    file_size_bytes=file_size_bytes,
                    sha256=digest,
                    downloaded_at=downloaded_at,
                    r2_key=r2_key,
                    r2_uploaded_at=utc_now_iso(),
                    source=source,
                )

            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(temp_path, target)
            return build_entry(
                set_num=set_num,
                name=name,
                year=year,
                pdf_url=pdf_url,
                status="downloaded",
                local_path=rel_path,
                file_size_bytes=file_size_bytes,
                sha256=digest,
                downloaded_at=downloaded_at,
                source=source,
            )
    except (DownloadError, SetNotFoundError, urllib.error.URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        print(f"failed: {set_num} ({exc})")
        return build_entry(
            set_num=set_num,
            name=name,
            year=year,
            pdf_url=seed.get("pdf_url"),
            status="failed",
            local_path=rel_path,
            file_size_bytes=None,
            sha256=None,
            downloaded_at=None,
            source=source,
        )


def run_dry(
    seeds: list[dict[str, Any]],
    *,
    year: int,
    report_path: Path,
    upload_r2: bool = False,
) -> dict[str, Any]:
    entries = [plan_seed(seed, year=year, upload_r2=upload_r2) for seed in seeds]
    report = {
        "agent": "pdf_harvester",
        "mode": "dry_run",
        "year": year,
        "upload_r2": upload_r2,
        "generated_at_utc": utc_now_iso(),
        "planned_downloads": sum(
            1 for entry in entries if entry["status"] in {"planned", "planned_r2"}
        ),
        "skipped_existing": sum(1 for entry in entries if entry["status"] == "skipped_exists"),
        "unresolved": sum(1 for entry in entries if entry["status"] == "unresolved"),
        "entries": entries,
    }

    for entry in entries:
        if entry["status"] in {"planned", "planned_r2"}:
            action = "PLAN_R2" if entry["status"] == "planned_r2" else "PLAN"
        elif entry["status"] == "skipped_exists":
            action = "SKIP"
        else:
            action = "UNRESOLVED"
        url_text = entry["pdf_url"] or "(no url)"
        destination = entry.get("r2_key") or entry["local_path"]
        print(f"{action}: {entry['set_num']} -> {destination} ({url_text})")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote dry-run report: {report_path.relative_to(ROOT_DIR)}")
    return report


def run_harvest(
    seeds: list[dict[str, Any]],
    *,
    year: int,
    manifest_path: Path,
    upload_r2: bool = False,
    delete_local_after_upload: bool = False,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path, year=year)
    manifest["agent"] = "pdf_harvester"
    manifest["year"] = year
    r2_config: dict[str, str] = {}
    r2_bucket = DEFAULT_R2_BUCKET
    r2_client = None
    if upload_r2:
        r2_config = load_r2_config()
        r2_bucket = r2_bucket_name(r2_config)
        r2_client = create_r2_client(r2_config)
        manifest["r2_bucket"] = r2_bucket

    for seed in seeds:
        entry = harvest_seed(
            seed,
            year=year,
            upload_r2=upload_r2,
            delete_local_after_upload=delete_local_after_upload,
            r2_client=r2_client,
            r2_bucket=r2_bucket,
        )
        upsert_manifest_entry(manifest, entry)

    manifest["updated_at_utc"] = utc_now_iso()
    save_manifest(manifest_path, manifest)
    print(f"updated manifest: {manifest_path.relative_to(ROOT_DIR)}")
    if upload_r2:
        manifest_key = manifest_r2_key(year)
        upload_manifest_to_r2(
            r2_client,
            manifest_path=manifest_path,
            bucket=r2_bucket,
            r2_key=manifest_key,
        )
        print(f"uploaded manifest:\nr2://{r2_bucket}/{manifest_key}")
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Harvest LEGO instruction PDFs from a seed list.",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=DEFAULT_YEAR,
        help="Release year for harvested PDFs (default: 2026).",
    )
    parser.add_argument(
        "--seed",
        type=Path,
        default=DEFAULT_SEED_PATH,
        help=f"Seed JSON path (default: {DEFAULT_SEED_PATH.relative_to(ROOT_DIR)}).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N seeds from the seed list.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve/plan downloads only; write dry-run report and do not download.",
    )
    parser.add_argument(
        "--upload-r2",
        action="store_true",
        help="Download to temp, upload PDFs to Cloudflare R2, and skip pdfs/{year}/ persistence.",
    )
    parser.add_argument(
        "--delete-local-after-upload",
        action="store_true",
        help="With --upload-r2, delete the temp PDF after a successful R2 upload.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    seed_path = args.seed if args.seed.is_absolute() else ROOT_DIR / args.seed
    if not seed_path.exists():
        print(f"seed file not found: {seed_path}", file=sys.stderr)
        return 1

    seed_year, seeds = load_seeds(seed_path)
    year = args.year or seed_year
    if args.limit is not None:
        seeds = seeds[: args.limit]

    if args.dry_run:
        report_path = ROOT_DIR / "reports" / f"pdf_harvest_{year}_dry_run.json"
        run_dry(
            seeds,
            year=year,
            report_path=report_path,
            upload_r2=args.upload_r2,
        )
        return 0

    manifest_path = INDEXES_DIR / f"pdf_manifest_{year}.json"
    run_harvest(
        seeds,
        year=year,
        manifest_path=manifest_path,
        upload_r2=args.upload_r2,
        delete_local_after_upload=args.delete_local_after_upload,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

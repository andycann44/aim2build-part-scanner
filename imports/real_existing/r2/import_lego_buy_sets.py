#!/usr/bin/env python3
"""
import_lego_buy_sets.py — Unified local import helper for Buy Sets tabs.

Fetches LEGO category pages, extracts set numbers, posts them to:
  POST /api/admin/buy-sets/import

MUST run locally on your Mac — LEGO blocks automated requests from server IPs.
Do NOT run on staging or production servers.

Sources and tab mapping:
  new_releases  → https://www.lego.com/en-gb/categories/new-sets-and-products
                  tab=new_releases, affiliate_ready=true, replace=true
  coming_soon   → https://www.lego.com/en-gb/categories/coming-soon
                  tab=new_releases (merged), display_status=coming_soon, replace=false
  retiring_soon → https://www.lego.com/en-gb/categories/last-chance-to-buy
                  tab=retiring_soon, affiliate_ready=true, replace=true
  whats_hot     → https://www.lego.com/en-gb/bestsellers
                  tab=whats_hot, affiliate_ready=true, replace=true

Usage:
  python backend/scripts/import_lego_buy_sets.py --source new_releases
  python backend/scripts/import_lego_buy_sets.py --source whats_hot
  python backend/scripts/import_lego_buy_sets.py --source retiring_soon
  python backend/scripts/import_lego_buy_sets.py --source all
  python backend/scripts/import_lego_buy_sets.py --source new_releases --dry-run
  python backend/scripts/import_lego_buy_sets.py --source retiring_soon --manual
  python backend/scripts/import_lego_buy_sets.py --source new_releases --api http://localhost:8000/api/admin/buy-sets/import

Environment:
  ADMIN_KEY or AIM2BUILD_ADMIN_KEY   Backend admin key (required unless --dry-run)

If Cloudflare blocks the request:
  1. Open the LEGO page in Safari/Chrome on your Mac.
  2. Wait for all products to load (scroll to bottom if needed).
  3. File → Save As → "Web Page, Complete" to get the fully-rendered HTML.
  4. Re-run the script; enter the saved .html file path when prompted.
     OR paste URLs/text directly and press Enter twice to finish.

No external dependencies — uses Python stdlib only.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.buy_sets_parts import resolve_num_parts  # noqa: E402
from app.lego_product_scrape import extract_piece_count_from_html, fetch_lego_piece_count  # noqa: E402
from app.paths import DATA_DIR  # noqa: E402

DEFAULT_CATALOG_DB = DATA_DIR / "lego_catalog.db"

# ── Source configuration ───────────────────────────────────────────────────────

@dataclass
class SourceConfig:
    name: str
    url: str
    tab: str
    replace: bool
    set_affiliate_ready: bool
    display_status_override: Optional[str]


SOURCES: dict[str, SourceConfig] = {
    "new_releases": SourceConfig(
        name="new_releases",
        url="https://www.lego.com/en-gb/categories/new-sets-and-products",
        tab="new_releases",
        replace=True,
        set_affiliate_ready=True,
        display_status_override=None,
    ),
    "coming_soon": SourceConfig(
        name="coming_soon",
        url="https://www.lego.com/en-gb/categories/coming-soon",
        tab="new_releases",      # merged into new_releases tab
        replace=False,           # upsert — don't clear tab already populated by new_releases
        set_affiliate_ready=True,
        display_status_override="coming_soon",
    ),
    "retiring_soon": SourceConfig(
        name="retiring_soon",
        url="https://www.lego.com/en-gb/categories/last-chance-to-buy",
        tab="retiring_soon",
        replace=True,
        set_affiliate_ready=True,
        display_status_override=None,
    ),
    "featured": SourceConfig(
        name="featured",
        url="https://www.lego.com/en-gb/categories/exclusives",
        tab="featured",
        replace=True,
        set_affiliate_ready=True,
        display_status_override=None,
    ),
    "whats_hot": SourceConfig(
        name="whats_hot",
        url="https://www.lego.com/en-gb/bestsellers",
        tab="whats_hot",
        replace=True,
        set_affiliate_ready=True,
        display_status_override=None,
    ),
}

ALL_SOURCES = ["new_releases", "coming_soon", "retiring_soon", "featured", "whats_hot"]

DEFAULT_API = "https://staging.aim2build.co.uk/api/admin/buy-sets/import"

FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ── Set number extraction ──────────────────────────────────────────────────────

# /en-gb/product/home-alone-21330 or /product/10294
_PRODUCT_URL_RE = re.compile(
    r'/product/(?:[a-z0-9][a-z0-9\-]*-)?(\d{4,6})(?=[/?#"\'<\s]|$)',
    re.IGNORECASE,
)

# Already in canonical form: 21330-1
_CANONICAL_RE = re.compile(r'\b(\d{4,6})-1\b')

# JSON field names carrying numeric set IDs
_JSON_FIELD_RE = re.compile(
    r'"(?:productId|setNumber|itemNumber|product_id|item_number|productNumber|productCode)"'
    r'\s*:\s*"?(\d{4,6})"?',
    re.IGNORECASE,
)


def _extract_from_next_data(html: str) -> list[str]:
    """Walk the Next.js __NEXT_DATA__ JSON blob for product IDs."""
    m = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        html, re.DOTALL,
    )
    if not m:
        return []

    raw_json = m.group(1)
    found: set[str] = set()

    # Primary: Apollo cache keys — "SingleVariantProduct:76417" embeds set number directly.
    for hit in re.findall(r'"SingleVariantProduct:(\d{4,6})"', raw_json):
        found.add(f"{hit}-1")

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return list(found)

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() in {
                    "productid", "setnumber", "itemnumber",
                    "product_id", "item_number", "productnumber",
                    "productcode",                               # LEGO Apollo field
                } and isinstance(v, (str, int)):
                    s = str(v).strip()
                    if re.fullmatch(r"\d{4,6}", s):
                        found.add(f"{s}-1")
                else:
                    walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    return list(found)


def extract_meta(html: str) -> list[dict]:
    """Extract name/image/price/pieces for each SingleVariantProduct from Apollo cache."""
    m = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        html, re.DOTALL,
    )
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []

    apollo = data.get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})
    if not apollo:
        return []

    records = []
    for key, svp in apollo.items():
        if not key.startswith("SingleVariantProduct:"):
            continue
        product_code = str(svp.get("productCode") or svp.get("id", "")).strip()
        if not re.fullmatch(r"\d{4,6}", product_code):
            continue

        pdp_path = svp.get("pdpPath", "") or ""
        variant_ref = svp.get("variant") or {}
        variant_id = variant_ref.get("id") if isinstance(variant_ref, dict) else None

        price_gbp: Optional[float] = None
        price_formatted: Optional[str] = None
        piece_count: Optional[int] = None
        availability_status: Optional[str] = None

        if variant_id:
            variant = apollo.get(variant_id) or {}
            price_ref = variant.get("price") or {}
            price_key = price_ref.get("id") if isinstance(price_ref, dict) else None
            if price_key:
                p = apollo.get(price_key) or {}
                price_gbp = p.get("formattedValue")
                price_formatted = p.get("formattedAmount")
            attrs_ref = variant.get("attributes") or {}
            attrs_key = attrs_ref.get("id") if isinstance(attrs_ref, dict) else None
            if attrs_key:
                a = apollo.get(attrs_key) or {}
                piece_count = a.get("pieceCount")
                availability_status = a.get("availabilityStatus")

        records.append({
            "set_num": f"{product_code}-1",
            "name": svp.get("name"),
            "img_url": svp.get("primaryImage"),
            "lego_url": f"https://www.lego.com{pdp_path}" if pdp_path else None,
            "price_gbp": price_gbp,
            "price_formatted": price_formatted,
            "availability_status": availability_status,
            "piece_count": piece_count,
        })

    return records


def enrich_meta_piece_counts(records: list[dict], catalog_db: Path = DEFAULT_CATALOG_DB) -> int:
    """Fill missing LEGO scrape piece counts from catalog/inventory fallbacks."""
    if not records or not catalog_db.exists():
        return 0

    con = sqlite3.connect(str(catalog_db))
    try:
        enriched = 0
        for rec in records:
            piece_count = rec.get("piece_count")
            if isinstance(piece_count, int) and piece_count > 0:
                continue
            set_num = (rec.get("set_num") or "").strip()
            if not set_num:
                continue
            resolved = resolve_num_parts(
                con,
                set_num,
                meta_piece_count=piece_count if isinstance(piece_count, int) else None,
            )
            if resolved:
                rec["piece_count"] = resolved
                enriched += 1
        return enriched
    finally:
        con.close()


def _record_piece_count(rec: Optional[dict]) -> Optional[int]:
    if not rec:
        return None
    value = rec.get("piece_count")
    if isinstance(value, int) and value > 0:
        return value
    return None


def scrape_missing_piece_counts(
    set_nums: list[str],
    records: list[dict],
    *,
    skip: bool = False,
    category_html: Optional[str] = None,
) -> int:
    """Final fallback: fetch LEGO product page JSON for sets still missing piece_count."""
    if skip or not set_nums:
        return 0

    meta_by_set = {
        (r.get("set_num") or "").strip(): r
        for r in records
        if (r.get("set_num") or "").strip()
    }
    con = sqlite3.connect(str(DEFAULT_CATALOG_DB)) if DEFAULT_CATALOG_DB.exists() else None
    scraped = 0
    try:
        for set_num in set_nums:
            sn = (set_num or "").strip()
            if not sn:
                continue
            rec = meta_by_set.get(sn)
            if _record_piece_count(rec):
                continue

            if con:
                resolved = resolve_num_parts(
                    con,
                    sn,
                    meta_piece_count=rec.get("piece_count") if rec else None,
                )
                if resolved:
                    if rec:
                        rec["piece_count"] = resolved
                    else:
                        rec = {"set_num": sn, "piece_count": resolved}
                        records.append(rec)
                        meta_by_set[sn] = rec
                    continue

            code = sn.split("-", 1)[0]
            if category_html:
                count = extract_piece_count_from_html(category_html, code)
                if count:
                    if rec:
                        rec["piece_count"] = count
                    else:
                        rec = {"set_num": sn, "piece_count": count}
                        records.append(rec)
                        meta_by_set[sn] = rec
                    scraped += 1
                    print(f"    Category HTML: {sn} -> {count} pcs")
                    continue

            lego_url = rec.get("lego_url") if rec else None
            print(f"    PDP scrape: {sn} ...")
            piece = fetch_lego_piece_count(sn, lego_url=lego_url)
            if piece:
                if rec:
                    rec["piece_count"] = piece
                else:
                    rec = {"set_num": sn, "piece_count": piece}
                    if lego_url:
                        rec["lego_url"] = lego_url
                    records.append(rec)
                    meta_by_set[sn] = rec
                scraped += 1
                print(f"      -> {piece} pcs")
            else:
                print("      -> piece count not found on LEGO page")
    finally:
        if con:
            con.close()
    return scraped


def extract_set_nums(content: str) -> list[str]:
    """Return sorted, deduplicated XXXXX-1 set numbers from HTML or plain text."""
    found: set[str] = set()

    # 1. Next.js JSON blob (best source — survives JS rendering when saved from browser)
    for s in _extract_from_next_data(content):
        found.add(s)

    # 2. Product URL patterns
    for m in _PRODUCT_URL_RE.finditer(content):
        found.add(f"{m.group(1)}-1")

    # 3. Canonical XXXXX-1 already present
    for m in _CANONICAL_RE.finditer(content):
        found.add(m.group(0))

    # 4. JSON field patterns (inline scripts outside __NEXT_DATA__)
    for m in _JSON_FIELD_RE.finditer(content):
        found.add(f"{m.group(1)}-1")

    return sorted(s for s in found if re.fullmatch(r"\d{4,6}-1", s))


# ── Cloudflare detection ───────────────────────────────────────────────────────

_CF_MARKERS = [
    "just a moment",
    "enable javascript and cookies",
    "cf-browser-verification",
    "checking if the site connection is secure",
    "cloudflare ray id",
    "please wait while we check your browser",
    "_cf_chl_opt",
]


def is_cloudflare_page(html: str) -> bool:
    lower = html.lower()
    return any(m in lower for m in _CF_MARKERS) and len(html) < 100_000


# ── Network ────────────────────────────────────────────────────────────────────

def fetch_page(url: str) -> Tuple[Optional[str], Optional[int]]:
    try:
        req = urllib.request.Request(url, headers=FETCH_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            status = resp.status
            raw = resp.read()
        # Decompress if gzip (server may still gzip even without Accept-Encoding)
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", errors="replace"), status
    except urllib.error.HTTPError as exc:
        print(f"    HTTP error: {exc.code} {exc.reason}")
        return None, exc.code
    except urllib.error.URLError as exc:
        print(f"    Network error: {exc.reason}")
        return None, None


def post_import(
    set_nums: list[str],
    tab: str,
    replace: bool,
    set_affiliate_ready: bool,
    display_status_override: Optional[str],
    api_url: str,
    admin_key: str,
) -> dict:
    payload: dict = {
        "tab": tab,
        "set_nums": set_nums,
        "replace": replace,
        "set_affiliate_ready": set_affiliate_ready,
        "source": "lego_scrape",
    }
    if display_status_override:
        payload["display_status_override"] = display_status_override

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=body,
        headers={"X-Admin-Key": admin_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_meta(records: list[dict], api_url: str, admin_key: str) -> dict:
    body = json.dumps({"records": records}).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=body,
        headers={"X-Admin-Key": admin_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ── Manual paste fallback ──────────────────────────────────────────────────────

def manual_paste_mode(source_name: str, url: str) -> Tuple[Optional[list[str]], list[dict]]:
    print()
    print("  ┌─ MANUAL PASTE MODE " + "─" * 40)
    print(f"  │  Source: {source_name}")
    print(f"  │  URL   : {url}")
    print("  │")
    print("  │  How to get the page HTML:")
    print("  │  1. Open the URL above in Safari or Chrome")
    print("  │  2. Scroll to the bottom to load all products")
    print("  │  3. File → Save As → 'Web Page, Complete'")
    print("  │  4. Enter the saved .html file path below")
    print("  │     OR paste URLs/set-numbers then press Enter twice")
    print("  └" + "─" * 50)
    print()
    raw = input("  File path or paste (q to skip this source): ").strip()
    if raw.lower() in {"q", "quit", "skip", ""}:
        return None, []

    p = Path(raw).expanduser()
    if p.exists() and p.is_file():
        print(f"  Reading: {p}  ({p.stat().st_size:,} bytes)")
        content = p.read_text(encoding="utf-8", errors="replace")
    else:
        lines = [raw]
        blanks = 0
        print("  Continue pasting (press Enter twice when done):")
        while blanks < 2:
            try:
                line = input()
            except EOFError:
                break
            if not line.strip():
                blanks += 1
            else:
                blanks = 0
                lines.append(line)
        content = "\n".join(lines)

    nums = extract_set_nums(content)
    meta_records = extract_meta(content)
    if not nums:
        print("  No set numbers found in provided content.")
        print("  Make sure products loaded before saving (not a blank/loading page).")
    return (nums or None), meta_records


# ── Single-source runner ───────────────────────────────────────────────────────

def run_source(
    cfg: SourceConfig,
    api_url: str,
    admin_key: str,
    no_replace: bool,
    dry_run: bool,
    force_manual: bool,
    skip_pdp_scrape: bool = False,
) -> bool:
    """Run import for one source. Returns True on success."""
    print()
    print(f"{'─'*62}")
    print(f"  Source : {cfg.name}")
    print(f"  URL    : {cfg.url}")
    print(f"  Tab    : {cfg.tab}"
          + (f"  (display_status={cfg.display_status_override})" if cfg.display_status_override else ""))
    replace = cfg.replace and not no_replace
    print(f"  Replace: {replace}   affiliate_ready: {cfg.set_affiliate_ready}")
    print()

    set_nums: Optional[list[str]] = None
    meta_records: list[dict] = []
    source_html: Optional[str] = None

    # ── Auto-fetch ────────────────────────────────────────────────────────────
    if not force_manual:
        print("  Fetching...")
        html, status = fetch_page(cfg.url)

        if html is None:
            print("  Could not reach LEGO page — switching to manual mode.")
        elif is_cloudflare_page(html):
            print(f"  HTTP {status}  ({len(html):,} chars)")
            print()
            print("  ⚠  Cloudflare blocked the request.")
            print("     This is expected when running from a home/office IP sometimes,")
            print("     and always from server IPs. Use manual mode below.")
        elif status == 200:
            print(f"  HTTP {status}  ({len(html):,} chars)")
            source_html = html
            set_nums = extract_set_nums(html)
            meta_records = extract_meta(html)
            if set_nums:
                print(f"  Extracted {len(set_nums)} set numbers, {len(meta_records)} meta records.")
            else:
                print("  Page fetched but no set numbers found (likely JS-rendered).")
                print("  Switching to manual mode.")
        else:
            print(f"  HTTP {status} — unexpected. Switching to manual mode.")

    # ── Manual fallback ───────────────────────────────────────────────────────
    if set_nums is None:
        set_nums, manual_meta = manual_paste_mode(cfg.name, cfg.url)
        if manual_meta:
            meta_records = manual_meta
        if set_nums is None:
            print(f"  Skipping {cfg.name}.")
            return False

    if set_nums:
        enriched = enrich_meta_piece_counts(meta_records)
        if enriched:
            print(f"  Enriched {enriched} meta record(s) with catalog piece counts.")
        scraped = scrape_missing_piece_counts(
            set_nums,
            meta_records,
            skip=dry_run or skip_pdp_scrape,
            category_html=source_html,
        )
        if scraped:
            print(f"  Scraped {scraped} piece count(s) from LEGO product pages.")

    # ── Report ────────────────────────────────────────────────────────────────
    print()
    print(f"  Found {len(set_nums)} set numbers:")
    for s in set_nums:
        print(f"    {s}")
    if meta_records:
        print(f"  Meta records ({len(meta_records)}):")
        for r in meta_records:
            set_num = r.get("set_num") or ""
            name = r.get("name") or r.get("title") or ""
            price = r.get("price_formatted") or r.get("price") or ""
            piece_count = r.get("piece_count") or r.get("num_parts") or 0
            print(
                f"    {set_num:10s}  {name[:40]:40s}  "
                f"{str(price):8s}  "
                f"{piece_count!s:>6} pcs"
            )

    if dry_run:
        print()
        print("  --dry-run: skipping POST.")
        return True

    if not set_nums:
        print("  Nothing to import.")
        return False

    # ── POST routing ──────────────────────────────────────────────────────────
    print()
    print("  Posting set routing to backend...")
    try:
        result = post_import(
            set_nums=set_nums,
            tab=cfg.tab,
            replace=replace,
            set_affiliate_ready=cfg.set_affiliate_ready,
            display_status_override=cfg.display_status_override,
            api_url=api_url,
            admin_key=admin_key,
        )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        print(f"  API error {exc.code}: {body}")
        return False
    except urllib.error.URLError as exc:
        print(f"  Connection error: {exc.reason}")
        return False

    print()
    print(f"  Routing result:")
    print(f"    ok            : {result.get('ok')}")
    print(f"    tab           : {result.get('tab')}")
    print(f"    inserted      : {result.get('inserted')}")
    deduped = result.get("deduped_from_new_releases", 0)
    if deduped:
        print(f"    deduped       : {deduped} set(s) removed from new_releases (retiring_soon priority)")
    not_in_cat = result.get("not_in_catalog", [])
    if not_in_cat:
        print(f"    not_in_catalog: {len(not_in_cat)} set(s) not in lego_catalog.db (shown via meta)")
        for s in not_in_cat:
            print(f"      {s}")
    else:
        print("    not_in_catalog: (none — all matched catalog)")

    # ── POST meta ─────────────────────────────────────────────────────────────
    meta_to_post = [
        r for r in meta_records
        if (r.get("set_num") or "").strip()
        and any(r.get(k) for k in ("name", "img_url", "lego_url", "price_formatted", "piece_count"))
    ]
    if meta_to_post:
        meta_url = api_url.rsplit("/", 1)[0] + "/meta"
        print()
        print(f"  Posting {len(meta_to_post)} meta records...")
        try:
            meta_result = post_meta(meta_to_post, meta_url, admin_key)
            print(f"    ok      : {meta_result.get('ok')}")
            print(f"    upserted: {meta_result.get('upserted')}")
        except urllib.error.HTTPError as exc:
            print(f"  Meta API error {exc.code}: {exc.read().decode('utf-8', errors='replace')[:200]}")
        except urllib.error.URLError as exc:
            print(f"  Meta connection error: {exc.reason}")

    return bool(result.get("ok"))


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import LEGO category pages into Buy Sets tabs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=[*sorted(SOURCES), "all"],
        help="Which source to run. 'all' runs new_releases, coming_soon, retiring_soon, featured, whats_hot in order.",
    )
    parser.add_argument("--api", default=DEFAULT_API, help="Backend admin import endpoint URL")
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="Upsert without clearing tab first (overrides per-source default).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract set numbers only — do not POST to backend.",
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Skip auto-fetch and go straight to manual paste mode.",
    )
    parser.add_argument(
        "--no-pdp-scrape",
        action="store_true",
        help="Skip per-set LEGO product page scrape for missing piece counts.",
    )
    args = parser.parse_args()

    admin_key = (
        os.environ.get("ADMIN_KEY") or os.environ.get("AIM2BUILD_ADMIN_KEY", "")
    ).strip()

    if not admin_key and not args.dry_run:
        sys.exit(
            "No admin key.\n"
            "Set ADMIN_KEY or AIM2BUILD_ADMIN_KEY env var, or use --dry-run."
        )

    sources_to_run = ALL_SOURCES if args.source == "all" else [args.source]

    print()
    print("Buy Sets Import")
    print(f"  API    : {args.api}")
    print(f"  Sources: {', '.join(sources_to_run)}")
    if args.dry_run:
        print("  Mode   : DRY RUN — will not POST")

    ok_count = 0
    for name in sources_to_run:
        success = run_source(
            cfg=SOURCES[name],
            api_url=args.api,
            admin_key=admin_key,
            no_replace=args.no_replace,
            dry_run=args.dry_run,
            force_manual=args.manual,
            skip_pdp_scrape=args.no_pdp_scrape,
        )
        if success:
            ok_count += 1

    print()
    print(f"{'─'*62}")
    print(f"  Done: {ok_count}/{len(sources_to_run)} source(s) succeeded.")
    if ok_count and not args.dry_run:
        print()
        print("  Verify:")
        print("    curl https://staging.aim2build.co.uk/api/buy-sets | python3 -m json.tool")


if __name__ == "__main__":
    main()

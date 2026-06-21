from __future__ import annotations

import logging
import sqlite3
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _normalise_set_id(set_num: str) -> str:
    set_id = (set_num or "").strip()
    if not set_id:
        return ""
    if "-" not in set_id:
        return f"{set_id}-1"
    return set_id


def _base_set_num(set_num: str) -> str:
    sn = _normalise_set_id(set_num)
    if "-" in sn:
        return sn.split("-", 1)[0]
    return sn


def _positive_int(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (name,),
    ).fetchone()
    return row is not None


def lookup_catalog_num_parts_exact(con: sqlite3.Connection, set_num: str) -> Optional[int]:
    sn = _normalise_set_id(set_num)
    if not sn:
        return None
    row = con.execute(
        "SELECT num_parts FROM sets WHERE set_num = ? LIMIT 1",
        (sn,),
    ).fetchone()
    if not row:
        return None
    return _positive_int(row[0])


def lookup_catalog_variant_row(
    con: sqlite3.Connection,
    set_num: str,
) -> Optional[tuple[str, int]]:
    base = _base_set_num(set_num)
    if not base:
        return None
    row = con.execute(
        """
        SELECT set_num, num_parts
        FROM sets
        WHERE set_num LIKE ?
          AND COALESCE(num_parts, 0) > 0
        ORDER BY year DESC, set_num ASC
        LIMIT 1
        """,
        (f"{base}-%",),
    ).fetchone()
    if not row:
        return None
    parts = _positive_int(row[1])
    if not parts:
        return None
    return (str(row[0]), parts)


def lookup_catalog_num_parts_variant(con: sqlite3.Connection, set_num: str) -> Optional[int]:
    row = lookup_catalog_variant_row(con, set_num)
    return row[1] if row else None


def _catalog_set_num_candidates(con: sqlite3.Connection, set_num: str) -> List[str]:
    sn = _normalise_set_id(set_num)
    if not sn:
        return []
    base = _base_set_num(sn)
    rows = con.execute(
        """
        SELECT set_num
        FROM sets
        WHERE set_num = ? OR set_num LIKE ?
        ORDER BY CASE WHEN set_num = ? THEN 0 ELSE 1 END,
                 year DESC,
                 set_num ASC
        """,
        (sn, f"{base}-%", sn),
    ).fetchall()
    seen: set[str] = set()
    out: List[str] = []
    for row in rows:
        candidate = (row[0] or "").strip()
        if candidate and candidate not in seen:
            seen.add(candidate)
            out.append(candidate)
    return out or [sn]


def lookup_inventory_part_count(con: sqlite3.Connection, set_num: str) -> Optional[int]:
    if not _table_exists(con, "inventories") or not _table_exists(con, "inventory_parts"):
        return None

    for candidate in _catalog_set_num_candidates(con, set_num):
        inv_row = con.execute(
            """
            SELECT inventory_id
            FROM inventories
            WHERE set_num = ?
            ORDER BY version ASC, inventory_id ASC
            LIMIT 1
            """,
            (candidate,),
        ).fetchone()
        if not inv_row:
            continue
        inv_id = int(inv_row[0])
        total_row = con.execute(
            """
            SELECT COALESCE(SUM(quantity), 0) AS total
            FROM inventory_parts
            WHERE inventory_id = ?
              AND COALESCE(is_spare, 0) = 0
            """,
            (inv_id,),
        ).fetchone()
        total = _positive_int(total_row[0] if total_row else 0)
        if total:
            return total
    return None


def lookup_meta_piece_count(con: sqlite3.Connection, set_num: str) -> Optional[int]:
    sn = _normalise_set_id(set_num)
    if not sn:
        return None
    try:
        row = con.execute(
            "SELECT piece_count FROM cfg.buy_sets_meta WHERE set_num = ? LIMIT 1",
            (sn,),
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    if not row:
        return None
    return _positive_int(row[0])


def diagnose_num_parts(
    con: sqlite3.Connection,
    set_num: str,
    *,
    catalog_num_parts: Optional[int] = None,
    meta_piece_count: Optional[int] = None,
) -> Dict[str, object]:
    sn = _normalise_set_id(set_num)
    exact_row = con.execute(
        "SELECT num_parts FROM sets WHERE set_num = ? LIMIT 1",
        (sn,),
    ).fetchone()
    exact_exists = exact_row is not None
    exact_parts = exact_row[0] if exact_row else None

    variant = lookup_catalog_variant_row(con, sn)
    inventory_sum = lookup_inventory_part_count(con, sn)
    meta_from_db = lookup_meta_piece_count(con, sn)
    effective_meta = _positive_int(meta_piece_count) or meta_from_db
    resolved = resolve_num_parts(con, sn)

    return {
        "set_num": sn,
        "catalog_exact_exists": exact_exists,
        "catalog_exact_num_parts": exact_parts,
        "catalog_variant_exists": variant is not None,
        "catalog_variant_set_num": variant[0] if variant else None,
        "catalog_variant_num_parts": variant[1] if variant else None,
        "meta_piece_count": effective_meta,
        "inventory_sum": inventory_sum,
        "resolved_num_parts": resolved,
    }


def format_num_parts_diagnosis(
    diag: Dict[str, object],
    *,
    tab: str = "",
    name: str = "",
    api_num_parts: Optional[int] = None,
) -> str:
    lines = [
        f"tab={tab or '-'}",
        f"set_num={diag.get('set_num')}",
        f"name={(name or '').strip()}",
        f"catalog_exact_exists={diag.get('catalog_exact_exists')}",
        f"catalog_exact_num_parts={diag.get('catalog_exact_num_parts')}",
        f"catalog_variant_exists={diag.get('catalog_variant_exists')}",
        f"catalog_variant_set_num={diag.get('catalog_variant_set_num')}",
        f"catalog_variant_num_parts={diag.get('catalog_variant_num_parts')}",
        f"buy_sets_meta.piece_count={diag.get('meta_piece_count')}",
        f"inventory_sum={diag.get('inventory_sum')}",
        f"resolved_num_parts={diag.get('resolved_num_parts')}",
    ]
    if api_num_parts is not None:
        lines.append(f"api_num_parts={api_num_parts}")
    return "\n".join(f"  {line}" for line in lines)


def resolve_num_parts(
    con: sqlite3.Connection,
    set_num: str,
    *,
    catalog_num_parts: Optional[int] = None,
    meta_piece_count: Optional[int] = None,
) -> int:
    """
    Preferred source order:
      1. Catalog sets.num_parts (exact set_num)
      2. LEGO scrape meta piece_count (buy_sets_meta)
      3. Catalog variant fallback (same base set number)
      4. Rebrickable inventory part sum
    """
    meta_from_db = lookup_meta_piece_count(con, set_num)
    for value in (
        _positive_int(catalog_num_parts),
        lookup_catalog_num_parts_exact(con, set_num),
        _positive_int(meta_piece_count),
        meta_from_db,
        lookup_catalog_num_parts_variant(con, set_num),
        lookup_inventory_part_count(con, set_num),
    ):
        if value:
            return value
    return 0

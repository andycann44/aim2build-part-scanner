from __future__ import annotations

import json
import logging
import re
import sqlite3
from collections import deque
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.paths import DATA_DIR


CONFIG_DB_PATH = str(DATA_DIR / "aim2build_config.db")
CATALOG_DB_PATH = str(DATA_DIR / "lego_catalog.db")
EXTERNAL_BRICKLINK_PART_MAP_PATH = Path(__file__).resolve().parents[2] / "frontend" / "src" / "data" / "bricklinkPartMap.external.generated.json"
LIVE_MARKETPLACE_MAPPING_TABLE = "marketplace_part_mappings"
MAX_RELATIONSHIP_CHAIN_DEPTH = 5
PART_COLOR_PAIR_CHUNK_SIZE = 200
DEBUG_BRICKLINK_PARTS = {"3957a", "4367", "60470a", "6141", "73983"}
RELATIONSHIP_MAPPING_SOURCES = {"part_relationships", "relationship_chain"}
TRAILING_VARIANT_ITEM_ID_RE = re.compile(r"^\d+[a-z]$")
logger = logging.getLogger(__name__)


def _cfg_db(config_db_path: Optional[str] = None) -> sqlite3.Connection:
    con = sqlite3.connect(config_db_path or CONFIG_DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("ATTACH DATABASE ? AS catalog", (CATALOG_DB_PATH,))
    return con


def normalize_source_part_num(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_source_element_id(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_source_color_id(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def build_part_color_lookup_key(part_num: str, color_id: int) -> str:
    return f"{normalize_source_part_num(part_num)}::{int(color_id)}"


def build_element_lookup_key(element_id: str) -> str:
    return f"element::{normalize_source_element_id(element_id)}"


def _table_exists(con: sqlite3.Connection, table_name: str) -> bool:
    row = con.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()
    return bool(row)


def _rows_to_mapping_dict(rows: list[sqlite3.Row]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        source_part_num = normalize_source_part_num(row["source_part_num"])
        out[source_part_num] = _normalize_part_level_mapping(
            source_part_num=source_part_num,
            bricklink_item_id=row["bricklink_item_id"],
            item_type=row["item_type"],
            mapping_kind=row["mapping_kind"],
            source=row["source"],
            confidence=row["confidence"],
            updated_at=row["updated_at"],
        )
    return out


@lru_cache(maxsize=1)
def _load_external_bricklink_part_map() -> Dict[str, Dict[str, Any]]:
    try:
        payload = json.loads(EXTERNAL_BRICKLINK_PART_MAP_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("[bricklink_mapping_db] external part map missing at %s", EXTERNAL_BRICKLINK_PART_MAP_PATH)
        return {}
    except json.JSONDecodeError:
        logger.exception("[bricklink_mapping_db] failed to parse external part map at %s", EXTERNAL_BRICKLINK_PART_MAP_PATH)
        return {}

    if not isinstance(payload, dict):
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    for raw_part_num, raw_entry in payload.items():
        part_num = normalize_source_part_num(raw_part_num)
        if not part_num or not isinstance(raw_entry, dict):
            continue
        out[part_num] = raw_entry
    return out


def _get_explicit_external_mapping(source_part_num: str) -> Optional[Dict[str, Any]]:
    external_entry = _load_external_bricklink_part_map().get(normalize_source_part_num(source_part_num))
    if not isinstance(external_entry, dict):
        return None
    if str(external_entry.get("mode") or "").strip() != "normalize":
        return None
    if str(external_entry.get("kind") or "").strip() != "external":
        return None

    bricklink_item_id = str(external_entry.get("itemId") or "").strip()
    if not bricklink_item_id:
        return None

    return {
        "bricklink_item_id": bricklink_item_id,
        "item_type": str(external_entry.get("itemType") or "P").strip() or "P",
        "mapping_kind": "external",
        "source": str(external_entry.get("reason") or "Rebrickable external_ids").strip() or "Rebrickable external_ids",
        "confidence": "high",
    }


def _normalize_part_level_mapping(
    *,
    source_part_num: str,
    bricklink_item_id: Any,
    item_type: Any,
    mapping_kind: Any,
    source: Any,
    confidence: Any,
    updated_at: Any,
    active: Optional[int] = None,
) -> Dict[str, Any]:
    normalized_source_part_num = normalize_source_part_num(source_part_num)
    normalized_item_id = str(bricklink_item_id or "").strip()
    normalized_source = str(source or "").strip()

    override = None
    if normalized_source in RELATIONSHIP_MAPPING_SOURCES:
        override = _get_explicit_external_mapping(normalized_source_part_num)
        if not override and TRAILING_VARIANT_ITEM_ID_RE.fullmatch(normalized_item_id):
            override = _get_explicit_external_mapping(normalized_item_id)

    out = {
        "source_part_num": normalized_source_part_num,
        "bricklink_item_id": normalized_item_id,
        "item_type": str(item_type or "P").strip() or "P",
        "mapping_kind": mapping_kind,
        "source": source,
        "confidence": confidence,
        "updated_at": updated_at,
    }

    if active is not None:
        out["active"] = int(active or 0)

    if override and override["bricklink_item_id"] != normalized_item_id:
        out["bricklink_item_id"] = override["bricklink_item_id"]
        out["item_type"] = override["item_type"]
        out["mapping_kind"] = override["mapping_kind"]
        out["source"] = override["source"]
        out["confidence"] = override["confidence"]

    return out


def _fetch_existing_mappings(con: sqlite3.Connection, part_nums: List[str]) -> Dict[str, Dict[str, Any]]:
    if not part_nums:
        return {}

    placeholders = ",".join("?" for _ in part_nums)
    rows = con.execute(
        f"""
        SELECT
          source_part_num,
          bricklink_item_id,
          item_type,
          mapping_kind,
          source,
          confidence,
          updated_at
        FROM bricklink_mappings
        WHERE source_part_num IN ({placeholders})
        """,
        part_nums,
    ).fetchall()
    return _rows_to_mapping_dict(rows)


def get_bricklink_part_color_mappings_by_rows(
    rows: List[Dict[str, Any]],
    config_db_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    normalized_rows: List[tuple[str, int]] = []
    seen: set[str] = set()

    for row in rows:
        part_num = normalize_source_part_num(row.get("part_num"))
        color_id = normalize_source_color_id(row.get("color_id"))
        if not part_num or color_id is None:
            continue
        key = build_part_color_lookup_key(part_num, color_id)
        if key in seen:
            continue
        seen.add(key)
        normalized_rows.append((part_num, color_id))

    if not normalized_rows:
        return {}

    with _cfg_db(config_db_path=config_db_path) as con:
        if not _table_exists(con, "bricklink_part_color_mappings"):
            return {}

        clauses = " OR ".join("(source_part_num = ? AND source_color_id = ?)" for _ in normalized_rows)
        params: list[Any] = []
        for part_num, color_id in normalized_rows:
            params.extend([part_num, color_id])

        fetched_rows = con.execute(
            f"""
            SELECT
              source_part_num,
              source_color_id,
              bricklink_item_id,
              bricklink_color_id,
              item_type,
              mapping_kind,
              source,
              confidence,
              updated_at
            FROM bricklink_part_color_mappings
            WHERE {clauses}
            """,
            params,
        ).fetchall()

    out: Dict[str, Dict[str, Any]] = {}
    for row in fetched_rows:
        source_part_num = normalize_source_part_num(row["source_part_num"])
        source_color_id = int(row["source_color_id"])
        out[build_part_color_lookup_key(source_part_num, source_color_id)] = {
            "source_part_num": source_part_num,
            "source_color_id": source_color_id,
            "bricklink_item_id": row["bricklink_item_id"],
            "bricklink_color_id": row["bricklink_color_id"],
            "item_type": row["item_type"] or "P",
            "mapping_kind": row["mapping_kind"],
            "source": row["source"],
            "confidence": row["confidence"],
            "updated_at": row["updated_at"],
        }

    return out


def get_marketplace_element_mappings_by_element_ids(
    marketplace: str,
    rows: List[Dict[str, Any]],
    config_db_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    normalized_marketplace = str(marketplace or "").strip().lower()
    if not normalized_marketplace:
        return {}

    requested_element_ids: List[str] = []
    seen: set[str] = set()

    for row in rows:
        element_id = normalize_source_element_id(row.get("element_id"))
        if not element_id or element_id in seen:
            continue
        seen.add(element_id)
        requested_element_ids.append(element_id)

    if not requested_element_ids:
        return {}

    with _cfg_db(config_db_path=config_db_path) as con:
        if not _table_exists(con, "marketplace_element_mappings"):
            return {}

        placeholders = ",".join("?" for _ in requested_element_ids)
        fetched_rows = con.execute(
            f"""
            SELECT
              marketplace,
              source_element_id,
              source_part_num,
              source_color_id,
              item_type,
              marketplace_item_id,
              marketplace_color_id,
              source,
              confidence,
              updated_at
            FROM marketplace_element_mappings
            WHERE marketplace = ?
              AND source_element_id IN ({placeholders})
            """,
            [normalized_marketplace, *requested_element_ids],
        ).fetchall()

    out: Dict[str, Dict[str, Any]] = {}
    for row in fetched_rows:
        source_element_id = normalize_source_element_id(row["source_element_id"])
        out[build_element_lookup_key(source_element_id)] = {
            "marketplace": str(row["marketplace"] or "").strip().lower(),
            "source_element_id": source_element_id,
            "source_part_num": normalize_source_part_num(row["source_part_num"]),
            "source_color_id": normalize_source_color_id(row["source_color_id"]),
            "marketplace_item_id": row["marketplace_item_id"],
            "marketplace_color_id": normalize_source_color_id(row["marketplace_color_id"]),
            "item_type": row["item_type"] or "P",
            "source": row["source"],
            "confidence": row["confidence"],
            "updated_at": row["updated_at"],
        }

    return out


def get_marketplace_part_mappings_by_element_ids(
    marketplace: str,
    rows: List[Dict[str, Any]],
    config_db_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    normalized_marketplace = str(marketplace or "").strip().lower()
    if not normalized_marketplace:
        return {}

    requested_element_ids: List[str] = []
    seen: set[str] = set()

    for row in rows:
        element_id = normalize_source_element_id(row.get("element_id"))
        if not element_id or element_id in seen:
            continue
        seen.add(element_id)
        requested_element_ids.append(element_id)

    if not requested_element_ids:
        return {}

    with _cfg_db(config_db_path=config_db_path) as con:
        if not _table_exists(con, LIVE_MARKETPLACE_MAPPING_TABLE):
            return {}

        placeholders = ",".join("?" for _ in requested_element_ids)
        fetched_rows = con.execute(
            f"""
            SELECT
              marketplace,
              source_element_id,
              source_part_num,
              source_color_id,
              item_type,
              marketplace_item_id,
              marketplace_color_id,
              match_level,
              source,
              confidence,
              active,
              updated_at,
              id
            FROM {LIVE_MARKETPLACE_MAPPING_TABLE}
            WHERE marketplace = ?
              AND active = 1
              AND match_level = 'element'
              AND source_element_id IN ({placeholders})
            ORDER BY updated_at DESC, id DESC
            """,
            [normalized_marketplace, *requested_element_ids],
        ).fetchall()

    out: Dict[str, Dict[str, Any]] = {}
    for row in fetched_rows:
        source_element_id = normalize_source_element_id(row["source_element_id"])
        lookup_key = build_element_lookup_key(source_element_id)
        if lookup_key in out:
            continue
        out[lookup_key] = {
            "marketplace": str(row["marketplace"] or "").strip().lower(),
            "source_element_id": source_element_id,
            "source_part_num": normalize_source_part_num(row["source_part_num"]),
            "source_color_id": normalize_source_color_id(row["source_color_id"]),
            "marketplace_item_id": row["marketplace_item_id"],
            "marketplace_color_id": normalize_source_color_id(row["marketplace_color_id"]),
            "item_type": row["item_type"] or "P",
            "match_level": row["match_level"],
            "source": row["source"],
            "confidence": row["confidence"],
            "active": int(row["active"] or 0),
            "updated_at": row["updated_at"],
        }

    return out


def _iter_part_color_pair_chunks(
    pairs: List[tuple[str, int]],
    chunk_size: int = PART_COLOR_PAIR_CHUNK_SIZE,
):
    for start in range(0, len(pairs), chunk_size):
        yield pairs[start:start + chunk_size]



def _build_part_color_where(chunk: List[tuple[str, int]]) -> tuple[str, List[Any]]:
    where = " OR ".join(["(source_part_num = ? AND source_color_id = ?)"] * len(chunk))
    params: List[Any] = []
    for part_num, color_id in chunk:
        params.extend([part_num, color_id])
    return where, params



def get_marketplace_part_color_mappings_by_rows(
    marketplace: str,
    rows: List[Dict[str, Any]],
    config_db_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    normalized_marketplace = str(marketplace or "").strip().lower()
    if not normalized_marketplace:
        return {}

    normalized_rows: List[tuple[str, int]] = []
    seen: set[str] = set()

    for row in rows:
        part_num = normalize_source_part_num(row.get("part_num"))
        color_id = normalize_source_color_id(row.get("color_id"))
        if not part_num or color_id is None:
            continue
        lookup_key = build_part_color_lookup_key(part_num, color_id)
        if lookup_key in seen:
            continue
        seen.add(lookup_key)
        normalized_rows.append((part_num, color_id))

    if not normalized_rows:
        return {}

    fetched_rows: List[sqlite3.Row] = []
    with _cfg_db(config_db_path=config_db_path) as con:
        if not _table_exists(con, LIVE_MARKETPLACE_MAPPING_TABLE):
            return {}

        for chunk in _iter_part_color_pair_chunks(normalized_rows):
            clauses, chunk_params = _build_part_color_where(chunk)
            fetched_rows.extend(
                con.execute(
                    f"""
                    SELECT
                      source_part_num,
                      source_color_id,
                      marketplace_item_id,
                      marketplace_color_id,
                      item_type,
                      match_level,
                      source,
                      confidence,
                      active,
                      updated_at,
                      id
                    FROM {LIVE_MARKETPLACE_MAPPING_TABLE}
                    WHERE marketplace = ?
                      AND active = 1
                      AND match_level = 'part_color'
                      AND ({clauses})
                    ORDER BY updated_at DESC, id DESC
                    """,
                    [normalized_marketplace, *chunk_params],
                ).fetchall()
            )

    out: Dict[str, Dict[str, Any]] = {}
    for row in fetched_rows:
        source_part_num = normalize_source_part_num(row["source_part_num"])
        source_color_id = int(row["source_color_id"])
        lookup_key = build_part_color_lookup_key(source_part_num, source_color_id)
        if lookup_key in out:
            continue
        out[lookup_key] = {
            "source_part_num": source_part_num,
            "source_color_id": source_color_id,
            "bricklink_item_id": row["marketplace_item_id"],
            "bricklink_color_id": normalize_source_color_id(row["marketplace_color_id"]),
            "item_type": row["item_type"] or "P",
            "mapping_kind": row["match_level"],
            "source": row["source"],
            "confidence": row["confidence"],
            "active": int(row["active"] or 0),
            "updated_at": row["updated_at"],
        }

    return out


def _get_parent_part_nums(con: sqlite3.Connection, child_part_num: str) -> List[str]:
    rows = con.execute(
        """
        SELECT DISTINCT parent_part_num
        FROM catalog.part_relationships
        WHERE child_part_num = ?
        ORDER BY parent_part_num ASC
        """,
        (child_part_num,),
    ).fetchall()
    return [normalize_source_part_num(row["parent_part_num"]) for row in rows if normalize_source_part_num(row["parent_part_num"])]


def _insert_relationship_chain_mapping(
    con: sqlite3.Connection,
    source_part_num: str,
    resolved_mapping: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    bricklink_item_id = str(resolved_mapping.get("bricklink_item_id") or "").strip()
    if not bricklink_item_id:
        return None

    item_type = str(resolved_mapping.get("item_type") or "P").strip() or "P"
    mapping_kind = str(resolved_mapping.get("mapping_kind") or "relationship_chain").strip() or "relationship_chain"

    con.execute(
        """
        INSERT INTO bricklink_mappings (
          source_part_num,
          bricklink_item_id,
          item_type,
          mapping_kind,
          source,
          confidence,
          updated_at
        )
        VALUES (?, ?, ?, ?, 'relationship_chain', 'medium', CURRENT_TIMESTAMP)
        ON CONFLICT(source_part_num) DO NOTHING
        """,
        (source_part_num, bricklink_item_id, item_type, mapping_kind),
    )
    row = con.execute(
        """
        SELECT
          source_part_num,
          bricklink_item_id,
          item_type,
          mapping_kind,
          source,
          confidence,
          updated_at
        FROM bricklink_mappings
        WHERE source_part_num = ?
        """,
        (source_part_num,),
    ).fetchone()
    return _rows_to_mapping_dict([row]).get(source_part_num) if row else None


def _resolve_via_relationship_chain(
    con: sqlite3.Connection,
    source_part_num: str,
) -> Optional[Dict[str, Any]]:
    visited: set[str] = {source_part_num}
    queue = deque([(source_part_num, 0)])
    candidate_mappings: Dict[str, Dict[str, Any]] = {}

    while queue:
        current_part_num, depth = queue.popleft()
        if depth >= MAX_RELATIONSHIP_CHAIN_DEPTH:
            continue

        parent_part_nums = _get_parent_part_nums(con, current_part_num)
        if not parent_part_nums:
            continue

        existing_parent_mappings = _fetch_existing_mappings(con, parent_part_nums)
        for parent_part_num in parent_part_nums:
            if parent_part_num in visited:
                continue
            visited.add(parent_part_num)

            mapping = existing_parent_mappings.get(parent_part_num)
            if mapping:
                candidate_key = "|".join(
                    [
                        str(mapping.get("bricklink_item_id") or ""),
                        str(mapping.get("item_type") or ""),
                        str(mapping.get("mapping_kind") or ""),
                    ]
                )
                candidate_mappings[candidate_key] = mapping
                continue

            queue.append((parent_part_num, depth + 1))

    if len(candidate_mappings) != 1:
        return None

    resolved_mapping = next(iter(candidate_mappings.values()))
    return _insert_relationship_chain_mapping(con, source_part_num, resolved_mapping)

def get_bricklink_mappings_by_part_nums(
    part_nums: List[str],
    config_db_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    normalized = [normalize_source_part_num(part_num) for part_num in part_nums]
    ordered_keys: List[str] = []
    seen: set[str] = set()

    for part_num in normalized:
        if not part_num or part_num in seen:
            continue
        seen.add(part_num)
        ordered_keys.append(part_num)

    if not ordered_keys:
        return {}

    with _cfg_db(config_db_path=config_db_path) as con:
        out = _fetch_existing_mappings(con, ordered_keys)
        missing = [part_num for part_num in ordered_keys if part_num not in out]

        for part_num in missing:
            resolved = _resolve_via_relationship_chain(con, part_num)
            if resolved:
                out[part_num] = resolved

        con.commit()

    debug_subset = {
        part_num: out[part_num]
        for part_num in ordered_keys
        if part_num in DEBUG_BRICKLINK_PARTS and part_num in out
    }
    if debug_subset:
        logger.warning(
            "[bricklink_mapping_db] returning mappings requested=%s mappings=%s",
            [part_num for part_num in ordered_keys if part_num in DEBUG_BRICKLINK_PARTS],
            debug_subset,
        )

    return out


def get_marketplace_part_mappings_by_part_nums(
    marketplace: str,
    part_nums: List[str],
    config_db_path: Optional[str] = None,
    allow_legacy_fallback: bool = True,
) -> Dict[str, Dict[str, Any]]:
    normalized_marketplace = str(marketplace or "").strip().lower()
    normalized = [normalize_source_part_num(part_num) for part_num in part_nums]
    ordered_keys: List[str] = []
    seen: set[str] = set()

    for part_num in normalized:
        if not part_num or part_num in seen:
            continue
        seen.add(part_num)
        ordered_keys.append(part_num)

    if not ordered_keys:
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    with _cfg_db(config_db_path=config_db_path) as con:
        if _table_exists(con, LIVE_MARKETPLACE_MAPPING_TABLE):
            placeholders = ",".join("?" for _ in ordered_keys)
            fetched_rows = con.execute(
                f"""
                SELECT
                  source_part_num,
                  marketplace_item_id,
                  marketplace_color_id,
                  item_type,
                  match_level,
                  source,
                  confidence,
                  active,
                  updated_at,
                  id
                FROM {LIVE_MARKETPLACE_MAPPING_TABLE}
                WHERE marketplace = ?
                  AND active = 1
                  AND match_level = 'part'
                  AND source_part_num IN ({placeholders})
                ORDER BY updated_at DESC, id DESC
                """,
                [normalized_marketplace, *ordered_keys],
            ).fetchall()

            for row in fetched_rows:
                source_part_num = normalize_source_part_num(row["source_part_num"])
                if source_part_num in out:
                    continue
                normalized_mapping = _normalize_part_level_mapping(
                    source_part_num=source_part_num,
                    bricklink_item_id=row["marketplace_item_id"],
                    item_type=row["item_type"],
                    mapping_kind=row["match_level"],
                    source=row["source"],
                    confidence=row["confidence"],
                    updated_at=row["updated_at"],
                    active=int(row["active"] or 0),
                )
                normalized_mapping["bricklink_color_id"] = normalize_source_color_id(row["marketplace_color_id"])
                out[source_part_num] = normalized_mapping

    missing = [part_num for part_num in ordered_keys if part_num not in out]
    if normalized_marketplace == "bricklink" and allow_legacy_fallback and missing:
        out.update(get_bricklink_mappings_by_part_nums(missing, config_db_path=config_db_path))

    return out


def get_marketplace_mapping_diagnostics(
    marketplace: str,
    config_db_path: Optional[str] = None,
) -> Dict[str, Any]:
    normalized_marketplace = str(marketplace or "").strip().lower()
    live_counts: Dict[str, int] = {}
    old_table_counts: Dict[str, int] = {}
    old_tables = [
        "bricklink_mappings",
        "bricklink_part_color_mappings",
        "bricklink_special_mappings",
        "marketplace_element_mappings",
        "bricklink_work_10312_1",
    ]

    with _cfg_db(config_db_path=config_db_path) as con:
        if _table_exists(con, LIVE_MARKETPLACE_MAPPING_TABLE):
            rows = con.execute(
                f"""
                SELECT match_level, COUNT(*) AS count
                FROM {LIVE_MARKETPLACE_MAPPING_TABLE}
                WHERE marketplace = ?
                GROUP BY match_level
                ORDER BY match_level ASC
                """,
                (normalized_marketplace,),
            ).fetchall()
            live_counts = {str(row["match_level"] or "unknown"): int(row["count"]) for row in rows}

        for table_name in old_tables:
            if not _table_exists(con, table_name):
                continue
            row = con.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
            old_table_counts[table_name] = int(row["count"]) if row else 0

    return {
        "marketplace": normalized_marketplace,
        "live_table": LIVE_MARKETPLACE_MAPPING_TABLE,
        "live_counts_by_match_level": live_counts,
        "old_table_counts": old_table_counts,
    }

from __future__ import annotations

from pathlib import Path
import sqlite3
import re

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any

from app.catalog_db import db, get_catalog_parts_for_set
from app.user_db import user_db
from app.selector_categories import get_selector_child_categories

router = APIRouter(tags=["catalog"])


# -----------------------------
# Helpers
# -----------------------------
def _normalize_set_id(raw: str) -> str:
    return (raw or "").strip()


def _safe_int_from_db(v: object) -> Optional[int]:
    """
    Defensive int parser for DB values.
    - Accepts ints, numeric strings (with whitespace).
    - Rejects None, "", "   ", non-digits, "cat:123", etc.
    - Never raises.
    """
    if v is None:
        return None
    if isinstance(v, int):
        return v
    s = str(v).strip()
    if not s:
        return None
    if not s.isdigit():
        return None
    try:
        return int(s)
    except Exception:
        return None


def _safe_int_or_zero(v: object) -> int:
    parsed = _safe_int_from_db(v)
    return parsed if parsed is not None else 0


def _load_category_overrides() -> Dict[int, Dict[str, Any]]:
    """
    Load category image overrides from aim2build_app.db brick_category_images.

    HARD RULE:
    - Must never crash due to bad helper table data.
    """
    overrides: Dict[int, Dict[str, Any]] = {}
    with user_db() as con:
        cur = con.execute(
            """
            SELECT key, label, img_url, sort_order, part_cat_id, is_enabled
            FROM cfg.brick_category_images
            """
        )
        rows = cur.fetchall()

    for r in rows:
        if hasattr(r, "keys"):
            part_cat_id = _safe_int_from_db(r["part_cat_id"])
            if part_cat_id is None:
                continue
            overrides[part_cat_id] = {
                "label": r["label"],
                "img_url": r["img_url"],
                "sort_order": _safe_int_or_zero(r["sort_order"]),
                "is_enabled": _safe_int_or_zero(r["is_enabled"]),
            }
        else:
            part_cat_id = _safe_int_from_db(r[4])
            if part_cat_id is None:
                continue
            overrides[part_cat_id] = {
                "label": r[1],
                "img_url": r[2],
                "sort_order": _safe_int_or_zero(r[3]),
                "is_enabled": _safe_int_or_zero(r[5]),
            }

    return overrides


def _load_parent_overrides() -> Dict[str, Dict[str, Any]]:
    """
    Load parent category overrides keyed by brick_category_images.key.
    """
    overrides: Dict[str, Dict[str, Any]] = {}
    with user_db() as con:
        cur = con.execute(
            """
            SELECT key, label, img_url, sort_order, is_enabled
            FROM cfg.brick_category_images
            WHERE part_cat_id IS NULL
            """
        )
        rows = cur.fetchall()
    for r in rows:
        if hasattr(r, "keys"):
            key = str(r["key"]).strip()
            overrides[key] = {
                "label": r["label"],
                "img_url": r["img_url"],
                "sort_order": _safe_int_or_zero(r["sort_order"]),
                "is_enabled": _safe_int_or_zero(r["is_enabled"]),
            }
        else:
            key = str(r[0]).strip()
            overrides[key] = {
                "label": r[1],
                "img_url": r[2],
                "sort_order": _safe_int_or_zero(r[3]),
                "is_enabled": _safe_int_or_zero(r[4]),
            }
    return overrides


@router.get("/categories/parents")
def catalog_category_parents() -> List[Dict[str, Any]]:
    """
    UI parent categories for Inventory Add flow.
    Source: aim2build_app.db brick_category_images (parent_key IS NULL)
    """
    out: List[Dict[str, Any]] = []
    with user_db() as con:
        rows = con.execute(
            """
            SELECT key, label, img_url, sort_order, part_cat_id, is_enabled
            FROM cfg.brick_category_images
            WHERE parent_key IS NULL
            """
        ).fetchall()

    for r in rows:
        if hasattr(r, "keys"):
            key = (str(r["key"]) if r["key"] is not None else "").strip()
            if not key:
                continue
            is_enabled = int(str(r["is_enabled"]).strip() or "0") if r["is_enabled"] is not None else 0
            if not is_enabled:
                continue
            out.append(
                {
                    "key": key,
                    "label": (r["label"] or key),
                    "img_url": r["img_url"],
                    "sort_order": int(str(r["sort_order"]).strip() or "0") if r["sort_order"] is not None else 0,
                    "part_cat_id": _safe_int_from_db(r["part_cat_id"]),
                }
            )
        else:
            key = (str(r[0]) if r[0] is not None else "").strip()
            if not key:
                continue
            is_enabled = int(str(r[5]).strip() or "0") if r[5] is not None else 0
            if not is_enabled:
                continue
            out.append(
                {
                    "key": key,
                    "label": (r[1] or key),
                    "img_url": r[2],
                    "sort_order": int(str(r[3]).strip() or "0") if r[3] is not None else 0,
                    "part_cat_id": _safe_int_from_db(r[4]),
                }
            )

    out.sort(key=lambda x: (x.get("sort_order", 0), str(x.get("label") or "").lower()))
    return out


@router.get("/categories/children")
def catalog_category_children(
    parent_key: Optional[str] = Query(None, description="UI parent key (e.g. brick/technic)"),
    parent_id: Optional[str] = Query(None, description="Legacy parent id"),
) -> List[Dict[str, Any]]:
    """
    UI children for Inventory Add flow.
    Source: aim2build_app.db brick_category_images WHERE parent_key = ?
    """
    pk = (parent_key or "").strip()
    pid = _safe_int_from_db(parent_id)
    if not pk and not pid:
        raise HTTPException(status_code=422, detail="Provide parent_key or parent_id")

    if pk:
        return get_selector_child_categories(pk)

    if not pid:
        return []

    out: List[Dict[str, Any]] = []
    with db() as con:
        rows = con.execute(
            """
            SELECT part_cat_id, name
            FROM part_categories
            WHERE parent_id = ?
            ORDER BY name
            """,
            (pid,),
        ).fetchall()

    for r in rows:
        part_cat_id = _safe_int_from_db(r["part_cat_id"] if hasattr(r, "keys") else r[0])
        if part_cat_id is None:
            continue
        label = r["name"] if hasattr(r, "keys") else r[1]
        out.append(
            {
                "part_cat_id": part_cat_id,
                "label": label,
                "img_url": None,
                "sort_order": 0,
            }
        )

    return out


def _is_printed_part_num(part_num: str) -> bool:
    # Rebrickable-style printed variants often contain 'pr' (e.g. 11477pr0028)
    return isinstance(part_num, str) and ("pr" in part_num)


def _base_part_num_for_printed(part_num: str) -> str:
    # 11477pr0028 -> 11477
    if not isinstance(part_num, str):
        return part_num
    m = re.match(r"^(\d+)", part_num)
    return m.group(1) if m else part_num


def _img_lookup_map(dbcon, keys):
    # keys: set of (part_num, color_id)
    # returns dict[(part_num,color_id)] = img_url
    if not keys:
        return {}
    part_nums = sorted({k[0] for k in keys})
    q_marks = ",".join(["?"] * len(part_nums))
    rows = dbcon.execute(
        f"SELECT part_num, color_id, img_url FROM element_images WHERE part_num IN ({q_marks})",
        part_nums,
    ).fetchall()
    out = {}
    for r in rows:
        out[(str(r["part_num"]), int(r["color_id"]))] = str(r["img_url"])
    return out


def _resolve_part_img_url_from_db(
    con,
    part_num: str,
    color_id: int,
) -> Optional[str]:
    """
    Image resolution (YOUR RULE):
      elements has columns: img_custom, img_rebrick, img_ldraw
      Priority: custom -> rebrick -> ldraw
      Elements can have multiple rows per (part_num,color_id) (multiple element_id),
      so we group and select the best non-empty string across the group.

    Returns:
      string URL or None
    """
    # Use NULLIF/TRIM to treat empty strings as NULL.
    row = con.execute(
        """
        SELECT
          COALESCE(
            MAX(NULLIF(TRIM(img_custom),  '')),
            MAX(NULLIF(TRIM(img_rebrick), '')),
            MAX(NULLIF(TRIM(img_ldraw),   ''))
          ) AS img_url
        FROM elements
        WHERE part_num = ?
          AND color_id = ?
        """,
        (part_num, int(color_id)),
    ).fetchone()

    if row and row["img_url"]:
        return str(row["img_url"])

    # Optional fallback: if elements table has no image fields populated for that key,
    # fall back to element_images.img_url if it exists.
    row2 = con.execute(
        """
        SELECT img_url
        FROM element_images
        WHERE part_num = ?
          AND color_id = ?
          AND img_url IS NOT NULL
          AND TRIM(img_url) <> ''
        LIMIT 1
        """,
        (part_num, int(color_id)),
    ).fetchone()

    if row2 and row2["img_url"]:
        return str(row2["img_url"])

    return None


# -----------------------------
# Part categories
# -----------------------------
@router.get("/part-categories")
def list_part_categories(parent_id: Optional[int] = Query(None)) -> List[Dict[str, Any]]:
    """
    List part categories filtered by parent_id.
    - parent_id omitted => top-level (parent_id IS NULL)
    - parent_id provided => children of that parent
    """
    with db() as con:
        if parent_id is None:
            cur = con.execute(
                """
                SELECT part_cat_id, name, parent_id
                FROM part_categories
                WHERE parent_id IS NULL
                ORDER BY name
                """
            )
        else:
            cur = con.execute(
                """
                SELECT part_cat_id, name, parent_id
                FROM part_categories
                WHERE parent_id = ?
                ORDER BY name
                """,
                (int(parent_id),),
            )
        rows = cur.fetchall()

    return [
        {
            "part_cat_id": int(r["part_cat_id"]),
            "name": r["name"],
            "parent_id": r["parent_id"],
        }
        for r in rows
    ]


@router.get("/part-categories/{part_cat_id:int}")
def get_part_category(part_cat_id: int) -> Dict[str, Any]:
    """
    Return a single part category row (for breadcrumb/back navigation).
    """
    with db() as con:
        cur = con.execute(
            """
            SELECT part_cat_id, name, parent_id
            FROM part_categories
            WHERE part_cat_id = ?
            LIMIT 1
            """,
            (int(part_cat_id),),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Category not found")

    return {
        "part_cat_id": int(row["part_cat_id"]),
        "name": row["name"],
        "parent_id": row["parent_id"],
    }


# -----------------------------
# Themes (for Minifig by Theme)
# -----------------------------
@router.get("/themes")
def list_themes(limit: int = Query(120, ge=1, le=500)) -> List[Dict[str, Any]]:
    """
    Return top themes with optional img_url.
    Uses themes + sets tables if present; otherwise distinct sets.theme_id.
    """
    with db() as con:
        has_themes = (
            con.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='themes' LIMIT 1"
            ).fetchone()
            is not None
        )

        if has_themes:
            rows = con.execute(
                """
                SELECT
                  t.theme_id AS theme_id,
                  t.name AS name,
                  COUNT(s.set_num) AS set_count,
                  (
                    SELECT s2.set_img_url
                    FROM sets s2
                    WHERE s2.theme_id = t.theme_id
                      AND s2.set_img_url IS NOT NULL
                      AND TRIM(s2.set_img_url) <> ''
                    ORDER BY s2.year DESC, s2.set_num DESC
                    LIMIT 1
                  ) AS img_url
                FROM themes t
                LEFT JOIN sets s ON s.theme_id = t.theme_id
                WHERE t.theme_id IS NOT NULL
                GROUP BY t.theme_id, t.name
                ORDER BY set_count DESC, LOWER(COALESCE(t.name, '')) ASC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT
                  s.theme_id AS theme_id,
                  NULL AS name,
                  COUNT(s.set_num) AS set_count,
                  (
                    SELECT s2.set_img_url
                    FROM sets s2
                    WHERE s2.theme_id = s.theme_id
                      AND s2.set_img_url IS NOT NULL
                      AND TRIM(s2.set_img_url) <> ''
                    ORDER BY s2.year DESC, s2.set_num DESC
                    LIMIT 1
                  ) AS img_url
                FROM sets s
                WHERE s.theme_id IS NOT NULL
                GROUP BY s.theme_id
                ORDER BY set_count DESC, s.theme_id ASC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()

    out: List[Dict[str, Any]] = []
    for r in rows:
        theme_id = int(r["theme_id"] if hasattr(r, "keys") else r[0])
        name = (r["name"] if hasattr(r, "keys") else r[1]) or f"Theme {theme_id}"
        img_url = r["img_url"] if hasattr(r, "keys") else r[3]
        out.append({"theme_id": theme_id, "name": name, "img_url": img_url})

    return out


@router.get("/part-categories/top")
def list_top_part_categories() -> List[Dict[str, Any]]:
    """
    Return top-level categories (parent_id IS NULL) excluding Duplo/Quatro/Primo.
    Also include a sample_img_url (element_images only).
    """
    with db() as con:
        cur = con.execute(
            """
            SELECT part_cat_id, name, parent_id
            FROM part_categories
            WHERE parent_id IS NULL
              AND lower(name) NOT LIKE '%duplo%'
              AND lower(name) NOT LIKE '%quatro%'
              AND lower(name) NOT LIKE '%primo%'
            ORDER BY name
            """
        )
        top_rows = cur.fetchall()

        out: List[Dict[str, Any]] = []
        for row in top_rows:
            cat_id = int(row["part_cat_id"])

            img_cur = con.execute(
                """
                WITH RECURSIVE cats(id) AS (
                  SELECT part_cat_id FROM part_categories WHERE part_cat_id = ?
                  UNION ALL
                  SELECT pc.part_cat_id
                  FROM part_categories pc
                  JOIN cats c ON pc.parent_id = c.id
                )
                SELECT ei.img_url
                FROM parts p
                JOIN cats c ON p.part_cat_id = c.id
                JOIN element_images ei ON ei.part_num = p.part_num
                WHERE ei.img_url IS NOT NULL
                  AND TRIM(ei.img_url) <> ''
                ORDER BY p.part_num ASC
                LIMIT 1
                """,
                (cat_id,),
            )
            img_row = img_cur.fetchone()
            sample_img = img_row["img_url"] if img_row else None

            out.append(
                {
                    "part_cat_id": cat_id,
                    "name": row["name"],
                    "parent_id": row["parent_id"],
                    "sample_img_url": sample_img,
                }
            )

    return out


# -----------------------------
# Parts by category
# -----------------------------
@router.get("/parts/by-category")
def parts_by_category(
    category_id: int = Query(..., description="part_cat_id to browse (includes descendants)"),
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> List[Dict[str, Any]]:
    """
    Return parts for a category and all its descendants.
    Images are strict from element_images (any colour, exact part_num match).
    """
    with db() as con:
        cur = con.execute(
            """
            WITH RECURSIVE cats(id) AS (
              SELECT part_cat_id FROM part_categories WHERE part_cat_id = ?
              UNION ALL
              SELECT pc.part_cat_id
              FROM part_categories pc
              JOIN cats c ON pc.parent_id = c.id
            )
            SELECT
              p.part_num,
              p.name AS part_name,
              p.part_cat_id,
              (
                SELECT COUNT(DISTINCT ei.color_id)
                FROM element_images ei
                WHERE ei.part_num = p.part_num
              ) AS color_count,
              (
                SELECT ei.color_id
                FROM element_images ei
                WHERE ei.part_num = p.part_num
                ORDER BY ei.color_id
                LIMIT 1
              ) AS default_color_id,
              (
                SELECT ei.img_url
                FROM element_images ei
                WHERE ei.part_num = p.part_num
                  AND ei.img_url IS NOT NULL
                  AND TRIM(ei.img_url) <> ''
                ORDER BY ei.color_id
                LIMIT 1
              ) AS default_img_url,
              (
                SELECT ei.img_url
                FROM element_images ei
                WHERE ei.part_num = p.part_num
                  AND ei.img_url IS NOT NULL
                  AND TRIM(ei.img_url) <> ''
                ORDER BY
                  CASE WHEN ei.color_id = 0 THEN 1 ELSE 0 END,
                  ei.color_id
                LIMIT 1
              ) AS part_img_url
            FROM parts p
            WHERE p.part_cat_id IN (SELECT id FROM cats)
            ORDER BY p.part_num
            LIMIT ? OFFSET ?
            """,
            (int(category_id), int(limit), int(offset)),
        )
        rows = cur.fetchall()

    return [
        {
            "part_num": r["part_num"],
            "part_name": r["part_name"],
            "part_cat_id": r["part_cat_id"],
            "color_count": r["color_count"],
            "default_color_id": r["default_color_id"],
            "default_img_url": r["default_img_url"],
            "part_img_url": r["part_img_url"],
        }
        for r in rows
    ]


@router.get("/part-image-random")
def part_image_random(
    part_num: str = Query(..., description="Part number to fetch a random image for"),
) -> Dict[str, Any]:
    """
    Return a random image URL for a part_num from element_images.
    """
    pn = (part_num or "").strip()
    if not pn:
        raise HTTPException(status_code=422, detail="Missing part_num")

    with db() as con:
        cur = con.execute(
            """
            SELECT eic.url
            FROM element_image_candidates eic
            JOIN elements e ON e.element_id = eic.element_id
            WHERE e.part_num = ?
              AND eic.url IS NOT NULL
              AND TRIM(eic.url) <> ''
            ORDER BY CASE WHEN eic.http_status = 200 THEN 0 ELSE 1 END, RANDOM()
            LIMIT 1
            """,
            (pn,),
        )
        row = cur.fetchone()

        if not row:
            cur = con.execute(
                """
                SELECT img_url
                FROM element_images
                WHERE part_num = ?
                  AND img_url IS NOT NULL
                  AND TRIM(img_url) <> ''
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (pn,),
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="No image found")

    img_url = row["url"] if hasattr(row, "keys") and "url" in row.keys() else (
        row["img_url"] if hasattr(row, "keys") else row[0]
    )
    return {"img_url": img_url}


# -----------------------------
# Parts for a set (uses catalog_db contract)
# -----------------------------
@router.get("/parts")
def get_catalog_parts(
    set: Optional[str] = Query(None, description="LEGO set number (alias: set_num, id)"),
    set_num: Optional[str] = Query(None),
    id: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    raw = set_num or set or id
    if not raw:
        raise HTTPException(
            status_code=400,
            detail="Provide one of set, set_num or id query parameters.",
        )

    set_id = _normalize_set_id(raw)
    base_parts = get_catalog_parts_for_set(set_id)

    if not base_parts:
        raise HTTPException(
            status_code=404,
            detail=f"No catalog parts found for set {set_id}",
        )

    enriched: List[Dict[str, Any]] = []
    with db() as con:
        for row in base_parts:
            part_num = str(row["part_num"])
            color_id = int(row["color_id"])
            qty = int(row["quantity"])

            img = _resolve_part_img_url_from_db(con, part_num, color_id)

            enriched.append(
                {
                    "part_num": part_num,
                    "color_id": color_id,
                    "quantity": qty,
                    "part_img_url": img,
                }
            )
    return enriched


# -----------------------------
# Search parts
# -----------------------------
@router.get("/parts/search")
def search_parts(
    q: Optional[str] = Query(None, description="Search term for part_num or name"),
    category_id: Optional[int] = Query(None, description="Filter by part_cat_id"),
    color_id: Optional[int] = Query(None, description="If provided, image lookup is STRICT to that colour."),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[Dict[str, Any]]:
    term = (q or "").strip()
    if not term:
        return []

    is_digits_only = term.isdigit()
    has_spaces = any(ch.isspace() for ch in term)

    clauses: List[str] = []
    params: List[Any] = []

    if category_id is not None:
        clauses.append("p.part_cat_id = ?")
        params.append(int(category_id))

    if not has_spaces:
        clauses.append("p.part_num LIKE ?")
        params.append(f"{term}%")
    else:
        ql = term.lower().strip()
        stop = {
            "brick",
            "bricks",
            "plate",
            "plates",
            "tile",
            "tiles",
            "with",
            "and",
            "or",
            "the",
            "a",
            "an",
            "of",
            "x",
            "by",
        }

        m = re.search(r"(\d+)\s*[xX]\s*(\d+)", ql)
        dims: List[str] = []
        if m:
            a, b = m.group(1), m.group(2)
            dims.append(f"{a} x {b}")
            dims.append(f"{b} x {a}")

        raw_tokens = re.findall(r"[a-z0-9]+", ql)
        tokens = [t for t in raw_tokens if t not in stop]

        for d in dims:
            clauses.append("lower(p.name) LIKE ?")
            params.append(f"%{d}%")

        for t in tokens:
            clauses.append("lower(p.name) LIKE ?")
            params.append(f"%{t}%")

        if not dims and not tokens:
            clauses.append("lower(p.name) LIKE ?")
            params.append(f"%{ql}%")

    where_sql = " WHERE " + " AND ".join(clauses)

    order_params: List[Any] = []
    if (not has_spaces) and is_digits_only:
        order_sql = """
        ORDER BY
          CASE
            WHEN p.part_num = ? THEN 0
            WHEN LENGTH(p.part_num) = ? THEN 1
            ELSE 2
          END,
          LENGTH(p.part_num) ASC,
          p.part_num ASC
        """
        order_params.extend([term, len(term) + 1])
    else:
        order_sql = "ORDER BY p.part_num ASC"

    if color_id is not None:
        img_sql = """
        (
          SELECT ei.img_url
          FROM element_images ei
          WHERE ei.part_num = p.part_num
            AND ei.color_id = ?
            AND ei.img_url IS NOT NULL
            AND TRIM(ei.img_url) <> ''
          LIMIT 1
        )
        """
        img_params: List[Any] = [int(color_id)]
    else:
        img_sql = """
        (
          SELECT ei.img_url
          FROM element_images ei
          WHERE ei.part_num = p.part_num
            AND ei.img_url IS NOT NULL
            AND TRIM(ei.img_url) <> ''
          ORDER BY ei.color_id ASC
          LIMIT 1
        )
        """
        img_params = []

    with db() as con:
        cur = con.execute(
            f"""
            SELECT
              p.part_num,
              p.name,
              CASE
                WHEN p.part_cat_id IN (
                  SELECT part_cat_id
                  FROM part_categories
                  WHERE lower(name) LIKE '%sticker%'
                )
                THEN NULL
                ELSE {img_sql}
              END AS part_img_url,
              CASE
                WHEN p.part_cat_id IN (
                  SELECT part_cat_id
                  FROM part_categories
                  WHERE lower(name) LIKE '%sticker%'
                )
                THEN 0
                WHEN {img_sql} IS NOT NULL THEN 1
                ELSE 0
              END AS image_exists
            FROM parts p
            {where_sql}
            {order_sql}
            LIMIT ?
            OFFSET ?
            """,
            (*img_params, *img_params, *params, *order_params, min(int(limit), 100), int(offset)),
        )
        rows = cur.fetchall()

    return [
        {
            "part_num": r["part_num"],
            "name": r["name"],
            "part_img_url": r["part_img_url"],
            "image_exists": int(r["image_exists"]) if r["image_exists"] is not None else 0,
        }
        for r in rows
    ]


# -----------------------------
# Elements by part
# -----------------------------
@router.get("/elements/by-part")
def get_elements_by_part(
    part_num: str = Query(..., description="Canonical part number (e.g. 3005 for 1x1 brick)"),
) -> List[Dict[str, Any]]:
    pn = (part_num or "").strip()
    if not pn:
        raise HTTPException(status_code=400, detail="part_num is required")

    with db() as con:
        cur = con.execute(
            """
            SELECT
              e.part_num AS part_num,
              e.color_id AS color_id,
              c.name     AS color_name,
              (
                SELECT ei.img_url
                FROM element_images ei
                WHERE ei.part_num = e.part_num
                  AND ei.color_id = e.color_id
                  AND ei.img_url IS NOT NULL
                  AND TRIM(ei.img_url) <> ''
                LIMIT 1
              ) AS img_url,
              MIN(e.element_id) AS element_id
            FROM elements e
            LEFT JOIN colors c
              ON c.color_id = e.color_id
            WHERE e.part_num = ?
              AND e.color_id IS NOT NULL
            GROUP BY e.part_num, e.color_id, c.name
            ORDER BY
              CASE
                WHEN (
                  SELECT ei2.img_url
                  FROM element_images ei2
                  WHERE ei2.part_num = e.part_num
                    AND ei2.color_id = e.color_id
                    AND ei2.img_url IS NOT NULL
                    AND TRIM(ei2.img_url) <> ''
                  LIMIT 1
                ) IS NOT NULL THEN 0
                ELSE 1
              END,
              LOWER(COALESCE(c.name, '')) ASC,
              e.color_id ASC
            """,
            (pn,),
        )
        rows = cur.fetchall()

    return [
        {
            "part_num": r["part_num"],
            "color_id": int(r["color_id"]) if r["color_id"] is not None else None,
            "color_name": r["color_name"],
            "img_url": r["img_url"],
            "element_id": r["element_id"],
        }
        for r in rows
    ]


# -----------------------------
# Colors
# -----------------------------
@router.get("/colors")
def list_colors(
    q: Optional[str] = Query(None, description="Filter by colour name or id."),
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
) -> List[Dict[str, Any]]:
    q_text = (q or "").strip()
    where_clauses: List[str] = ["color_id >= 0"]
    params: List[Any] = []

    if q_text:
        clauses = ["LOWER(name) LIKE ?"]
        params.append(f"%{q_text.lower()}%")
        if re.fullmatch(r"-?\\d+", q_text):
            clauses.append("color_id = ?")
            params.append(int(q_text))
        where_clauses.append("(" + " OR ".join(clauses) + ")")

    where_sql = "WHERE " + " AND ".join(where_clauses)

    with db() as con:
        cur = con.execute(
            f"""
            SELECT color_id, name, rgb, is_trans
            FROM colors
            {where_sql}
            ORDER BY color_id ASC
            LIMIT ?
            OFFSET ?
            """,
            (*params, int(limit), int(offset)),
        )
        rows = cur.fetchall()

    out: List[Dict[str, Any]] = []
    for r in rows:
        rgb = str(r["rgb"] or "").strip().upper()
        out.append(
            {
                "color_id": int(r["color_id"]),
                "name": r["name"],
                "rgb": rgb,
                "hex": f"#{rgb}" if rgb else "",
                "is_trans": int(r["is_trans"] or 0),
            }
        )
    return out


# -----------------------------
# Image stats/sample
# -----------------------------
@router.get("/images/stats")
def catalog_image_stats():
    with db() as con:
        row = con.execute(
            """
            SELECT
              COUNT(*) AS total,
              SUM(is_dead=1) AS dead,
              SUM(is_dead=0) AS live,
              SUM(last_checked IS NULL OR last_checked=0) AS unchecked
            FROM element_images
            """
        ).fetchone()
        return dict(row) if row else {"total": 0, "dead": 0, "live": 0, "unchecked": 0}


@router.get("/images/sample")
def catalog_image_sample(
    mode: str = "best",  # best | raw
    filter: str = "live",  # live | dead | unchecked | all
    limit: int = 100,
    offset: int = 0,
):
    with db() as con:
        if mode == "best":
            base = """
            SELECT part_num, color_id, img_url
            FROM element_best_image
            """
            where = ""
            params: List[Any] = []
        else:
            base = """
            SELECT part_num, color_id, img_url
            FROM element_images
            """
            where = "WHERE img_url IS NOT NULL AND TRIM(img_url) <> ''"
            params = []

            if filter == "live":
                where += " AND is_dead=0"
            elif filter == "dead":
                where += " AND is_dead=1"
            elif filter == "unchecked":
                where += " AND (last_checked IS NULL OR last_checked=0)"
            elif filter == "all":
                pass

        sql = f"""
        {base}
        {where}
        ORDER BY part_num ASC, color_id ASC, img_url ASC
        LIMIT ? OFFSET ?
        """
        rows = con.execute(sql, (int(limit), int(offset), *params)).fetchall()
        return [dict(r) for r in rows]


# ------------------------------------------------------------
# V2: BuildabilityDetails-safe parts endpoint (NOW DB-DRIVEN)
# - No local filesystem checks
# - Uses elements image priority: custom -> rebrick -> ldraw
# - Falls back to /static/missing.png
# ------------------------------------------------------------
@router.get("/parts-v2")
def get_parts_v2(set: str = None, set_num: str = None, id: str = None):
    set_id = (set or set_num or id or "").strip()
    if not set_id:
        return []

    if "-" not in set_id and set_id.isdigit():
        set_id = f"{set_id}-1"

    base_parts = get_catalog_parts_for_set(set_id) or []

    out = []
    with db() as con:
        for r in base_parts:
            pn = str(r["part_num"])
            cid = int(r["color_id"])

            disp = _resolve_part_img_url_from_db(con, pn, cid)
            if not disp:
                disp = "/static/missing.png"

            out.append(
                {
                    "set_num": set_id,
                    "part_num": pn,
                    "color_id": cid,
                    "quantity": int(r.get("quantity") or 0),
                    "part_img_url": disp,
                    "display_img_url": disp,
                    "is_printed": bool(_is_printed_part_num(pn)),
                    "is_sticker": False,
                }
            )
    return out

@router.get("/parts/used-in")
def parts_used_in(
    part_num: str = Query(...),
    color_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Return sets that use a given part.
    Read-only. Uses lego_catalog.db only.
    """
    with db() as con:
        params = [part_num]

        sql = """
        SELECT
          sp.set_num,
          s.name,
          s.year,
          s.img_url,
          s.num_parts,
          SUM(sp.qty_per_set) AS qty_needed
        FROM set_parts sp
        JOIN sets s ON s.set_num = sp.set_num
        WHERE sp.part_num = ?
        """

        if color_id is not None:
            sql += " AND sp.color_id = ? "
            params.append(color_id)

        sql += """
        GROUP BY sp.set_num, s.name, s.year, s.img_url, s.num_parts
        ORDER BY s.year DESC, sp.set_num
        LIMIT ?
        """

        params.append(limit)

        rows = con.execute(sql, params).fetchall()

        return [
            {
                "set_num": r["set_num"],
                "name": r["name"],
                "year": r["year"],
                "img_url": r["img_url"],
                "num_parts": r["num_parts"],
                "qty_needed": r["qty_needed"],
            }
            for r in rows
        ]

    return out


# -----------------------------
# Popular parts by category
# -----------------------------

_POPULAR_CAT_IDS: Dict[str, List[int]] = {
    "bricks":  [11, 37, 20, 5],
    "plates":  [14, 49, 21, 9],
    "tiles":   [19, 67, 15],
    "slopes":  [3, 6],
    "technic": [46, 51, 55, 8, 54, 12, 52, 40, 53, 26, 25],
    "wheels":  [29],
    "windows": [16, 47],
    "animals": [28, 74, 75],
    "other":   [24, 32, 7, 18, 23, 31, 34, 30],
}

# Colorful color_ids tried in rotation order; offset per part via hash so
# the grid mixes colours deterministically rather than always returning the
# lowest (usually Black/Dark-grey) color_id.
_PREFERRED_COLOR_IDS: List[int] = [
    4,   # Red
    1,   # Blue
    14,  # Yellow
    15,  # White
    2,   # Green
    19,  # Tan
    70,  # Reddish Brown
    25,  # Orange
    71,  # Light Bluish Gray
    72,  # Dark Bluish Gray
    0,   # Black  (last — least colourful)
]


def _part_hash(part_num: str) -> int:
    h = 0
    for ch in part_num:
        h = (h * 31 + ord(ch)) & 0xffff
    return h


def _pick_color_image(
    by_color: Dict[int, Dict[str, Any]],
    part_num: str,
) -> Dict[str, Any]:
    """
    Select one image dict from by_color using a hash-based rotation over the
    preferred color list.  Falls back to the first available color if no
    preferred color has an image for this part.
    """
    if not by_color:
        return {"img_url": None, "color_id": None, "color_name": None}

    offset = _part_hash(part_num) % len(_PREFERRED_COLOR_IDS)
    for i in range(len(_PREFERRED_COLOR_IDS)):
        cid = _PREFERRED_COLOR_IDS[(offset + i) % len(_PREFERRED_COLOR_IDS)]
        if cid in by_color:
            return by_color[cid]

    return next(iter(by_color.values()))


@router.get("/parts/popular")
def parts_popular(
    category: str = Query(..., description="UI category slug"),
    limit: int = Query(50, ge=1, le=200),
) -> List[Dict[str, Any]]:
    """
    Return the most-used parts in a category, ranked by distinct set appearances.
    Images are selected via hash-based rotation over preferred LEGO colour ids so
    the grid shows mixed real colours rather than always the lowest color_id.
    Read-only against lego_catalog.db.
    """
    cat_ids = _POPULAR_CAT_IDS.get(category.strip().lower())
    if not cat_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown category '{category}'. Valid: {sorted(_POPULAR_CAT_IDS)}",
        )

    cat_ph = ",".join("?" * len(cat_ids))

    with db() as con:
        # Step 1 — ranked parts by usage count
        ranked = con.execute(
            f"""
            SELECT
                sp.part_num,
                p.name,
                COUNT(DISTINCT sp.set_num) AS usage_count
            FROM set_parts sp
            JOIN parts p ON p.part_num = sp.part_num
            WHERE p.part_cat_id IN ({cat_ph})
              AND COALESCE(p.is_obsolete, 0) = 0
            GROUP BY sp.part_num, p.name
            ORDER BY usage_count DESC
            LIMIT ?
            """,
            (*cat_ids, int(limit)),
        ).fetchall()

        if not ranked:
            return []

        part_nums = [r["part_num"] for r in ranked]
        img_ph = ",".join("?" * len(part_nums))

        # Step 2 — batch-fetch all real images for these parts from elements + colors
        img_rows = con.execute(
            f"""
            SELECT
                e.part_num,
                e.color_id,
                c.name AS color_name,
                COALESCE(
                    NULLIF(TRIM(e.img_custom),  ''),
                    NULLIF(TRIM(e.img_rebrick), ''),
                    NULLIF(TRIM(e.img_ldraw),   '')
                ) AS img_url
            FROM elements e
            LEFT JOIN colors c ON c.color_id = e.color_id
            WHERE e.part_num IN ({img_ph})
              AND (
                  NULLIF(TRIM(e.img_custom),  '') IS NOT NULL
               OR NULLIF(TRIM(e.img_rebrick), '') IS NOT NULL
               OR NULLIF(TRIM(e.img_ldraw),   '') IS NOT NULL
              )
            ORDER BY e.part_num, e.color_id
            """,
            part_nums,
        ).fetchall()

    # Step 3 — group images by part_num → {color_id: row_dict}
    images_by_part: Dict[str, Dict[int, Dict[str, Any]]] = {}
    for r in img_rows:
        pn  = r["part_num"]
        cid = int(r["color_id"])
        if pn not in images_by_part:
            images_by_part[pn] = {}
        if cid not in images_by_part[pn]:          # keep first row per (part, color)
            images_by_part[pn][cid] = {
                "img_url":    r["img_url"],
                "color_id":   cid,
                "color_name": r["color_name"],
            }

    # Step 4 — assemble response with hash-selected colour image
    return [
        {
            "part_num":    r["part_num"],
            "name":        r["name"],
            "usage_count": int(r["usage_count"]),
            **_pick_color_image(images_by_part.get(r["part_num"], {}), r["part_num"]),
        }
        for r in ranked
    ]


# ─── Category search helpers ───────────────────────────────────────────────────

_SET_NUM_RE = re.compile(r'^\d{3,6}(-\d+)?$')


def _normalize_set_num(raw: str) -> str:
    s = raw.strip()
    return s if '-' in s else f"{s}-1"


def _fetch_popular_for_cat_ids(cat_ids: List[int], limit: int) -> List[Dict[str, Any]]:
    """Popular parts for an explicit list of part_cat_ids, ranked by distinct set count."""
    cat_ph = ",".join("?" * len(cat_ids))
    with db() as con:
        ranked = con.execute(
            f"""
            SELECT
                sp.part_num,
                p.name,
                COUNT(DISTINCT sp.set_num) AS usage_count
            FROM set_parts sp
            JOIN parts p ON p.part_num = sp.part_num
            WHERE p.part_cat_id IN ({cat_ph})
              AND COALESCE(p.is_obsolete, 0) = 0
            GROUP BY sp.part_num, p.name
            ORDER BY usage_count DESC
            LIMIT ?
            """,
            (*cat_ids, int(limit)),
        ).fetchall()

        if not ranked:
            return []

        part_nums = [r["part_num"] for r in ranked]
        img_ph = ",".join("?" * len(part_nums))

        img_rows = con.execute(
            f"""
            SELECT
                e.part_num,
                e.color_id,
                c.name AS color_name,
                COALESCE(
                    NULLIF(TRIM(e.img_custom),  ''),
                    NULLIF(TRIM(e.img_rebrick), ''),
                    NULLIF(TRIM(e.img_ldraw),   '')
                ) AS img_url
            FROM elements e
            LEFT JOIN colors c ON c.color_id = e.color_id
            WHERE e.part_num IN ({img_ph})
              AND (
                  NULLIF(TRIM(e.img_custom),  '') IS NOT NULL
               OR NULLIF(TRIM(e.img_rebrick), '') IS NOT NULL
               OR NULLIF(TRIM(e.img_ldraw),   '') IS NOT NULL
              )
            ORDER BY e.part_num, e.color_id
            """,
            part_nums,
        ).fetchall()

    images_by_part: Dict[str, Dict[int, Dict[str, Any]]] = {}
    for r in img_rows:
        pn  = r["part_num"]
        cid = int(r["color_id"])
        if pn not in images_by_part:
            images_by_part[pn] = {}
        if cid not in images_by_part[pn]:
            images_by_part[pn][cid] = {
                "img_url":    r["img_url"],
                "color_id":   cid,
                "color_name": r["color_name"],
            }

    return [
        {
            "part_num":         r["part_num"],
            "name":             r["name"],
            "usage_count":      int(r["usage_count"]),
            "source_reason":    "Popular in category",
            "matched_set_num":  None,
            "matched_set_name": None,
            **_pick_color_image(images_by_part.get(r["part_num"], {}), r["part_num"]),
        }
        for r in ranked
    ]


def _collect_set_parts(
    con: sqlite3.Connection,
    set_row: Any,
    cat_ids: List[int],
    cat_ph: str,
    results: Dict[str, Dict[str, Any]],
    limit: int,
) -> None:
    """Append parts from set_row that match cat_ids into results (first-seen wins)."""
    set_num  = set_row["set_num"]
    set_name = set_row["name"] or set_num
    rows = con.execute(
        f"""
        SELECT sp.part_num, p.name, sp.qty_per_set
        FROM set_parts sp
        JOIN parts p ON p.part_num = sp.part_num
        WHERE sp.set_num = ?
          AND p.part_cat_id IN ({cat_ph})
          AND COALESCE(p.is_obsolete, 0) = 0
        ORDER BY sp.qty_per_set DESC
        LIMIT ?
        """,
        (set_num, *cat_ids, limit),
    ).fetchall()
    for r in rows:
        pn = r["part_num"]
        if pn not in results:
            results[pn] = {
                "part_num":         pn,
                "name":             r["name"],
                "usage_count":      0,
                "source_reason":    f"From set: {set_name}",
                "matched_set_num":  set_num,
                "matched_set_name": set_name,
            }


@router.get("/parts/category-search")
def parts_category_search(
    category: str = Query(..., description="Category slug (same keys as /parts/popular)"),
    q: str = Query("", description="Search term: part name, part number, set number or set name"),
    limit: int = Query(50, ge=1, le=200),
) -> List[Dict[str, Any]]:
    """
    Smart category-scoped search.

    - q empty      → popular parts for the category (identical to /parts/popular).
    - q = set num  → parts from that set filtered to the category, ranked by qty.
    - q = text     → set name matches (category-filtered) first, then part name/num matches.

    Read-only. Does not mutate any table.
    """
    cat_ids = _POPULAR_CAT_IDS.get(category.strip().lower())
    if not cat_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown category '{category}'. Valid: {sorted(_POPULAR_CAT_IDS)}",
        )

    q = (q or "").strip()
    if not q:
        return _fetch_popular_for_cat_ids(cat_ids, limit)

    cat_ph   = ",".join("?" * len(cat_ids))
    results: Dict[str, Dict[str, Any]] = {}   # part_num → entry; first-seen wins

    with db() as con:
        # ── Branch A: explicit set number ─────────────────────────────────────
        if _SET_NUM_RE.match(q):
            set_num = _normalize_set_num(q)
            set_row = con.execute(
                "SELECT set_num, name FROM sets WHERE set_num = ? LIMIT 1",
                (set_num,),
            ).fetchone()
            if set_row:
                _collect_set_parts(con, set_row, cat_ids, cat_ph, results, limit)

        # ── Branch B: free text ───────────────────────────────────────────────
        else:
            ql = q.lower()

            # B1. Set name search first — more specific intent, shown at top
            set_rows = con.execute(
                """
                SELECT set_num, name
                FROM sets
                WHERE lower(name) LIKE ?
                ORDER BY
                  CASE WHEN lower(name) = ? THEN 0 ELSE 1 END,
                  year DESC
                LIMIT 20
                """,
                (f"%{ql}%", ql),
            ).fetchall()
            for sr in set_rows:
                _collect_set_parts(con, sr, cat_ids, cat_ph, results, limit)

            # B2. Part name / part_num match within category (appended after set results)
            part_rows = con.execute(
                f"""
                SELECT p.part_num, p.name
                FROM parts p
                WHERE p.part_cat_id IN ({cat_ph})
                  AND COALESCE(p.is_obsolete, 0) = 0
                  AND (
                      lower(p.part_num) LIKE ?
                   OR lower(p.name)     LIKE ?
                  )
                ORDER BY
                  CASE
                    WHEN lower(p.part_num) = ? THEN 0
                    WHEN lower(p.name)     = ? THEN 1
                    ELSE 2
                  END,
                  p.part_num
                LIMIT ?
                """,
                (*cat_ids, f"%{ql}%", f"%{ql}%", ql, ql, limit),
            ).fetchall()
            for r in part_rows:
                pn = r["part_num"]
                if pn not in results:
                    name_lc = (r["name"] or "").lower()
                    reason  = "Matched part name" if ql in name_lc else "Matched part number"
                    results[pn] = {
                        "part_num":         pn,
                        "name":             r["name"],
                        "usage_count":      0,
                        "source_reason":    reason,
                        "matched_set_num":  None,
                        "matched_set_name": None,
                    }

        if not results:
            return []

        # ── Batch-fetch images for all collected parts ─────────────────────────
        part_nums = list(results.keys())
        img_ph    = ",".join("?" * len(part_nums))

        img_rows = con.execute(
            f"""
            SELECT
                e.part_num,
                e.color_id,
                c.name AS color_name,
                COALESCE(
                    NULLIF(TRIM(e.img_custom),  ''),
                    NULLIF(TRIM(e.img_rebrick), ''),
                    NULLIF(TRIM(e.img_ldraw),   '')
                ) AS img_url
            FROM elements e
            LEFT JOIN colors c ON c.color_id = e.color_id
            WHERE e.part_num IN ({img_ph})
              AND (
                  NULLIF(TRIM(e.img_custom),  '') IS NOT NULL
               OR NULLIF(TRIM(e.img_rebrick), '') IS NOT NULL
               OR NULLIF(TRIM(e.img_ldraw),   '') IS NOT NULL
              )
            ORDER BY e.part_num, e.color_id
            """,
            part_nums,
        ).fetchall()

    images_by_part: Dict[str, Dict[int, Dict[str, Any]]] = {}
    for r in img_rows:
        pn  = r["part_num"]
        cid = int(r["color_id"])
        if pn not in images_by_part:
            images_by_part[pn] = {}
        if cid not in images_by_part[pn]:
            images_by_part[pn][cid] = {
                "img_url":    r["img_url"],
                "color_id":   cid,
                "color_name": r["color_name"],
            }

    out: List[Dict[str, Any]] = []
    for pn, entry in results.items():
        out.append({**entry, **_pick_color_image(images_by_part.get(pn, {}), pn)})
        if len(out) >= limit:
            break

    return out

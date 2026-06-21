from pathlib import Path
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import sqlite3
import os


# Path to lego_catalog.db
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "lego_catalog.db"


def ensure_catalog_indexes() -> None:
    """
    Create performance indexes on lego_catalog.db if they don't already exist.
    Safe to call at startup — all statements use CREATE INDEX IF NOT EXISTS.
    element_images is a VIEW so it cannot be indexed; the underlying elements
    table already has idx_elements_part_color(part_num, color_id).
    """
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_parts_part_cat_id "
            "ON parts(part_cat_id)"
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_set_parts_part_num "
            "ON set_parts(part_num)"
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_set_parts_set_num "
            "ON set_parts(set_num)"
        )
        con.commit()
    finally:
        con.close()


@contextmanager
def db():
    """Simple SQLite connection helper with row dicts."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


def _normalise_set_id(set_num: str) -> str:
    """
    Normalise a set id so both "70618" and "70618-1" work.
    Returns an empty string for falsey input.
    """
    set_id = (set_num or "").strip()
    if not set_id:
        return ""
    if "-" not in set_id:
        return f"{set_id}-1"
    return set_id


def _apply_color_to_img_url(url: Optional[str], color_id: int) -> Optional[str]:
    """
    Given a Rebrickable part_img_url and a desired color_id,
    rewrite the URL so that the colour segment matches color_id.
    Handles both .../parts/<color>/... and .../parts/ldraw/<color>/...
    """
    if not url:
        return None

    try:
        parts = url.split("/")
        # colour is usually the last numeric segment before the filename
        for i in range(len(parts) - 2, -1, -1):
            if parts[i].isdigit():
                parts[i] = str(color_id)
                break
        return "/".join(parts)
    except Exception:
        return url


def _abs_img(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    base = (os.getenv("A2B_STATIC_BASE_URL") or "").rstrip("/")
    if not base:
        return url
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if not url.startswith("/"):
        url = "/" + url
    return base + url


def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (name,),
    ).fetchone()
    return row is not None


def _view_exists(con: sqlite3.Connection, name: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='view' AND name=? LIMIT 1",
        (name,),
    ).fetchone()
    return row is not None


def _latest_inventory_id(con: sqlite3.Connection, set_id: str) -> Optional[int]:
    row = con.execute(
        """
        SELECT inventory_id
        FROM inventories
        WHERE set_num = ?
        ORDER BY version DESC, inventory_id DESC
        LIMIT 1
        """,
        (set_id,),
    ).fetchone()
    if not row:
        return None
    return int(row["inventory_id"])


def get_catalog_parts_for_set(set_num: str) -> List[Dict[str, Any]]:
    """
    Return parts for a set from the SQLite catalog.

    IMPORTANT CONTRACT (used by buildability):
      each row must include: part_num, color_id, quantity (int)

    Rules:
      - strict identity is (part_num, color_id)
      - use latest inventory only when sourcing from inventories/inventory_parts
      - exclude spares with COALESCE(is_spare, 0) = 0
      - do NOT join element_images before quantity aggregation
      - attach at most one image per (part_num, color_id)

    Image source of truth:
      element_images(part_num, color_id, img_url)
    """
    set_id = _normalise_set_id(set_num)
    if not set_id:
        return []

    with db() as con:
        rows: List[sqlite3.Row] = []

        # Prefer instruction-derived requirements if present (currently disabled)
        # Kept here for future use, but intentionally not active.
        if False and _table_exists(con, "instruction_set_requirements"):
            cur = con.execute(
                """
                WITH img_one AS (
                    SELECT
                        part_num,
                        color_id,
                        MIN(img_url) AS img_url
                    FROM element_images
                    GROUP BY part_num, color_id
                )
                SELECT
                    r.part_num,
                    r.color_id,
                    CAST(r.qty AS INTEGER) AS quantity,
                    img_one.img_url AS img_url
                FROM instruction_set_requirements AS r
                LEFT JOIN img_one
                  ON img_one.part_num = r.part_num
                 AND img_one.color_id = r.color_id
                WHERE r.set_num = ?
                ORDER BY r.part_num, r.color_id
                """,
                (set_id,),
            )
            rows = cur.fetchall()

        # Preferred live path: latest inventory + raw inventory_parts
        elif _table_exists(con, "inventories") and _table_exists(con, "inventory_parts"):
            inv_id = _latest_inventory_id(con, set_id)
            if inv_id is None:
                return []

            cur = con.execute(
                """
                WITH qty_rows AS (
                    SELECT
                        ip.part_num,
                        ip.color_id,
                        SUM(ip.quantity) AS quantity
                    FROM inventory_parts AS ip
                    WHERE ip.inventory_id = ?
                      AND COALESCE(ip.is_spare, 0) = 0
                    GROUP BY ip.part_num, ip.color_id
                ),
                img_one AS (
                    SELECT
                        ei.part_num,
                        ei.color_id,
                        MIN(ei.img_url) AS img_url
                    FROM element_images AS ei
                    GROUP BY ei.part_num, ei.color_id
                )
                SELECT
                    q.part_num,
                    q.color_id,
                    CAST(q.quantity AS INTEGER) AS quantity,
                    img_one.img_url AS img_url
                FROM qty_rows AS q
                LEFT JOIN img_one
                  ON img_one.part_num = q.part_num
                 AND img_one.color_id = q.color_id
                ORDER BY q.part_num, q.color_id
                """,
                (inv_id,),
            )
            rows = cur.fetchall()

        # Fallback: use set_parts if present
        elif _table_exists(con, "set_parts"):
            cur = con.execute(
                """
                WITH img_one AS (
                    SELECT
                        ei.part_num,
                        ei.color_id,
                        MIN(ei.img_url) AS img_url
                    FROM element_images AS ei
                    GROUP BY ei.part_num, ei.color_id
                )
                SELECT
                    sp.part_num,
                    sp.color_id,
                    CAST(sp.qty_per_set AS INTEGER) AS quantity,
                    COALESCE(img_one.img_url, sp.part_img_url) AS img_url
                FROM set_parts AS sp
                LEFT JOIN img_one
                  ON img_one.part_num = sp.part_num
                 AND img_one.color_id = sp.color_id
                WHERE sp.set_num = ?
                ORDER BY sp.part_num, sp.color_id
                """,
                (set_id,),
            )
            rows = cur.fetchall()

        # Last resort: inventory_parts_summary, keeping the same contract
        elif _table_exists(con, "inventory_parts_summary"):
            cur = con.execute(
                """
                WITH img_one AS (
                    SELECT
                        ei.part_num,
                        ei.color_id,
                        MIN(ei.img_url) AS img_url
                    FROM element_images AS ei
                    GROUP BY ei.part_num, ei.color_id
                )
                SELECT
                    s.part_num,
                    s.color_id,
                    CAST(s.quantity AS INTEGER) AS quantity,
                    img_one.img_url AS img_url
                FROM inventory_parts_summary AS s
                LEFT JOIN img_one
                  ON img_one.part_num = s.part_num
                 AND img_one.color_id = s.color_id
                WHERE s.set_num = ?
                ORDER BY s.part_num, s.color_id
                """,
                (set_id,),
            )
            rows = cur.fetchall()

        else:
            return []

    return [
        {
            "part_num": row["part_num"],
            "color_id": int(row["color_id"]),
            "quantity": int(row["quantity"] or 0),
            "part_img_url": _abs_img(row["img_url"]),
            "img_url": _abs_img(row["img_url"]),
        }
        for row in rows
    ]


def get_set_num_parts(set_num: str) -> int:
    """
    Return the official num_parts from the sets table for display purposes.
    """
    set_id = _normalise_set_id(set_num)
    if not set_id:
        return 0

    with db() as con:
        cur = con.execute(
            """
            SELECT num_parts
            FROM sets
            WHERE set_num = ?
            """,
            (set_id,),
        )
        row = cur.fetchone()

    if row is None:
        return 0
    return int(row["num_parts"] or 0)
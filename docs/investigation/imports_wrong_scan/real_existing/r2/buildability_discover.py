from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query

from app.catalog_db import db
from app.routers.auth import User, get_current_user
from app.routers.buildability import _load_inventory_json  # MUST match compare source


# IMPORTANT:
# Do NOT set a prefix here. main.py already mounts this router under /api/buildability.
router = APIRouter(tags=["buildability"])


def _cdn_set_img_url(set_num: str) -> str | None:
    """
    LOCKED RULE: Images must resolve via Aim2Build CDN (Cloudflare/R2) only.
    We do NOT return Rebrickable URLs to clients.
    """
    sn = (set_num or "").strip()
    if not sn:
        return None
    return f"https://img.aim2build.co.uk/static/set_images/{sn}.jpg"


@router.get("/discover")
def discover_buildability(
    min_coverage: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=40),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Discover sets you can build using EXACT SAME rules as /compare:

    - Requirements: v_set_requirements (SUM(quantity))
    - Strict match: (part_num, color_id)
    - total_have: SUM(min(inv_qty, need_qty))
    - coverage = total_have / total_needed

    PLUS:
    - Excludes via lego_catalog.db tables:
      * set_filters (enabled=1 -> excluded)
      * theme_filters (enabled=1 -> excluded)
    - Temporary minifig-name guard (kept as extra safety)
    """

    inv_rows = _load_inventory_json(current_user.id)

    inv_triplets: List[tuple[str, int, int]] = []
    for r in inv_rows:
        pn = str(r.get("part_num") or "").strip()
        if not pn:
            continue
        cid = int(r.get("color_id", 0))  # color_id=0 is valid
        qty = int(r.get("qty_total", r.get("qty", r.get("quantity", 0))))
        if qty > 0:
            inv_triplets.append((pn, cid, qty))

    if not inv_triplets:
        return []

    with db() as con:
        # temp inventory (strict part_num+color_id)
        con.execute("DROP TABLE IF EXISTS temp_inv")
        con.execute(
            """
            CREATE TEMP TABLE temp_inv (
                part_num TEXT NOT NULL,
                color_id INTEGER NOT NULL,
                qty INTEGER NOT NULL
            )
            """
        )
        con.executemany(
            "INSERT INTO temp_inv(part_num, color_id, qty) VALUES (?, ?, ?)",
            inv_triplets,
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_temp_inv_pc ON temp_inv(part_num, color_id)"
        )

        sql = """
        WITH common_parts AS (
            SELECT sp.part_num
            FROM set_parts sp
            GROUP BY sp.part_num
            HAVING COUNT(DISTINCT sp.set_num) > 1000
        ),
        filtered_inv AS (
            SELECT part_num, color_id, qty
            FROM temp_inv
            WHERE part_num NOT IN (SELECT part_num FROM common_parts)
        ),
        candidate_sets AS (
            SELECT r.set_num
            FROM v_set_requirements r
            JOIN filtered_inv i
            ON i.part_num = r.part_num
            AND i.color_id = r.color_id
            WHERE COALESCE(r.quantity, 0) > 0
            GROUP BY r.set_num
            HAVING COUNT(*) >= 3
        ),
        agg AS (
            SELECT
                r.set_num AS set_num,
                SUM(r.quantity) AS total_needed,
                SUM(MIN(COALESCE(ti.qty, 0), r.quantity)) AS total_have
            FROM v_set_requirements r
            JOIN candidate_sets cs
            ON cs.set_num = r.set_num
            LEFT JOIN temp_inv ti
            ON ti.part_num = r.part_num
            AND ti.color_id = r.color_id
            WHERE COALESCE(r.quantity, 0) > 0
            GROUP BY r.set_num
        )
        SELECT
            a.set_num AS set_num,
            s.name AS name,
            s.year AS year,
            s.img_url AS img_url,
            s.num_parts AS num_parts,
            s.theme_id AS theme_id,
            a.total_needed AS total_needed,
            a.total_have AS total_have,
            CASE
            WHEN a.total_needed > 0 THEN (1.0 * a.total_have) / a.total_needed
            ELSE 0.0
            END AS coverage
        FROM agg a
        JOIN sets s
        ON s.set_num = a.set_num
        WHERE a.total_needed >= 53
        AND (CASE
                WHEN a.total_needed > 0 THEN (1.0 * a.total_have) / a.total_needed
                ELSE 0.0
            END) >= ?
        AND NOT EXISTS (
                SELECT 1 FROM set_filters sf
                WHERE sf.enabled = 1
                AND sf.set_num = a.set_num
            )
        AND NOT EXISTS (
                SELECT 1 FROM theme_filters tf
                WHERE tf.enabled = 1
                AND tf.theme_id = s.theme_id
            )
        ORDER BY coverage DESC, a.total_needed DESC, a.set_num ASC
        LIMIT ?
        """

        params = (float(min_coverage), int(limit))
        cur = con.execute(sql, params)
        rows = cur.fetchall()

        out: List[Dict[str, Any]] = []
        for row in rows:
            # con.row_factory usually yields dict-like rows; keep fallback tuple unpack
            try:
                set_num = str(row["set_num"])
                out.append(
                    {
                        "set_num": set_num,
                        "name": row["name"],
                        "year": int(row["year"]) if row["year"] is not None else None,
                        # IMPORTANT: always return Aim2Build CDN URL (not Rebrickable)
                        "img_url": _cdn_set_img_url(set_num),
                        "num_parts": int(row["num_parts"]) if row["num_parts"] is not None else None,
                        "theme_id": int(row["theme_id"]) if row["theme_id"] is not None else None,
                        "total_needed": int(row["total_needed"]) if row["total_needed"] is not None else 0,
                        "total_have": int(row["total_have"]) if row["total_have"] is not None else 0,
                        "coverage": float(row["coverage"]) if row["coverage"] is not None else 0.0,
                    }
                )
            except Exception:
                (
                    set_num,
                    name,
                    year,
                    img_url,
                    num_parts,
                    theme_id,
                    total_needed,
                    total_have,
                    coverage,
                ) = row
                sn = str(set_num)
                out.append(
                    {
                        "set_num": sn,
                        "name": name,
                        "year": int(year) if year is not None else None,
                        # IMPORTANT: always return Aim2Build CDN URL (not Rebrickable)
                        "img_url": _cdn_set_img_url(sn),
                        "num_parts": int(num_parts) if num_parts is not None else None,
                        "theme_id": int(theme_id) if theme_id is not None else None,
                        "total_needed": int(total_needed) if total_needed is not None else 0,
                        "total_have": int(total_have) if total_have is not None else 0,
                        "coverage": float(coverage) if coverage is not None else 0.0,
                    }
                )

        return out

from typing import Optional
import re

from app.catalog_db import db


def _variant_base_part_num(part_num: str) -> Optional[str]:
    """
    Image-only fallback:
    3001b -> 3001
    3001c01 -> 3001
    2456pb01 -> 2456
    """
    pn = (part_num or "").strip()

    m = re.match(r"^(\d+)", pn)
    if not m:
        return None

    base = m.group(1)
    return base if base != pn else None


def get_strict_element_image(part_num: str, color_id: int) -> Optional[str]:
    """
    STRICT image lookup using lego_catalog.db element_images table.

    Rules:
      - Exact lookup first
      - Variant fallback second
      - No colour fallback
    """

    if not part_num or color_id is None:
        return None

    def lookup(pn: str) -> Optional[str]:
        with db() as con:
            cur = con.execute(
                """
                SELECT img_url
                FROM element_images
                WHERE part_num = ?
                  AND color_id = ?
                  AND img_url IS NOT NULL
                  AND TRIM(img_url) != ''
                LIMIT 1
                """,
                (pn, color_id),
            )
            row = cur.fetchone()

        if not row:
            return None

        return row["img_url"]

    exact = lookup(part_num)
    if exact:
        return exact

    base_part = _variant_base_part_num(part_num)
    if base_part:
        return lookup(base_part)

    return None
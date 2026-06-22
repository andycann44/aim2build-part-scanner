from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
from collections import deque


TINY_CATALOG = [
    {"part_num": "3010", "name": "Brick 1 x 4", "stud_x": 1, "stud_y": 4, "type": "brick"},
    {"part_num": "3001", "name": "Brick 2 x 4", "stud_x": 2, "stud_y": 4, "type": "brick"},
    {"part_num": "3004", "name": "Brick 1 x 2", "stud_x": 1, "stud_y": 2, "type": "brick"},
    {"part_num": "3003", "name": "Brick 2 x 2", "stud_x": 2, "stud_y": 2, "type": "brick"},
    {"part_num": "3039", "name": "Slope 45 2 x 2", "stud_x": 2, "stud_y": 2, "type": "slope"},
    {"part_num": "3040", "name": "Slope 45 2 x 1", "stud_x": 2, "stud_y": 1, "type": "slope"},
]


def _bbox_features(path: Path) -> dict:
    img = Image.open(path).convert("RGBA")
    bbox = img.getbbox()
    if not bbox:
        return {"width": 0, "height": 0, "ratio": 0}
    l, t, r, b = bbox
    width = max(1, r - l)
    height = max(1, b - t)
    ratio = max(width, height) / max(1, min(width, height))
    return {"width": width, "height": height, "ratio": ratio}


def _components(mask):
    w, h = mask.size
    mp = mask.load()
    seen = set()
    comps = []

    for sy in range(h):
        for sx in range(w):
            if mp[sx, sy] == 0 or (sx, sy) in seen:
                continue
            q = deque([(sx, sy)])
            seen.add((sx, sy))
            pts = []

            while q:
                x, y = q.popleft()
                pts.append((x, y))
                for nx, ny in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
                    if 0 <= nx < w and 0 <= ny < h and mp[nx, ny] and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        q.append((nx, ny))

            if pts:
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                comps.append({
                    "area": len(pts),
                    "bbox": (min(xs), min(ys), max(xs)+1, max(ys)+1),
                    "cx": sum(xs) / len(xs),
                    "cy": sum(ys) / len(ys),
                    "w": max(xs) - min(xs) + 1,
                    "h": max(ys) - min(ys) + 1,
                })

    return comps


def _detect_studs(path: Path) -> dict:
    """
    V1 stud detector:
    Uses bright rim/text highlights on stud tops.
    This is not OCR yet; it detects repeated stud-top blobs.
    """
    img = Image.open(path).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    rgb = Image.new("RGB", img.size, "black")
    rgb.paste(img, mask=img.getchannel("A"))

    gray = ImageOps.grayscale(rgb)
    # Pull out specular/text/rim highlights from black studs.
    mask = gray.point(lambda p: 255 if p > 55 else 0)
    mask = mask.filter(ImageFilter.MinFilter(3))
    mask = mask.filter(ImageFilter.MaxFilter(7))

    comps = _components(mask)

    # Filter to likely stud highlight groups.
    likely = []
    img_area = img.width * img.height
    for c in comps:
        if c["area"] < 20:
            continue
        if c["area"] > img_area * 0.08:
            continue
        if c["w"] > img.width * 0.45 or c["h"] > img.height * 0.45:
            continue
        likely.append(c)

    # Merge nearby blobs into stud centres.
    centres = []
    for c in sorted(likely, key=lambda x: x["area"], reverse=True):
        cx, cy = c["cx"], c["cy"]
        if all((cx - x) ** 2 + (cy - y) ** 2 > 35 ** 2 for x, y in centres):
            centres.append((cx, cy))

    # Cap sensible count for first scanner tests.
    centres = centres[:12]

    # Detect row/column layout from centres.
    layout = "unknown"
    if len(centres) >= 2:
        xs = [c[0] for c in centres]
        ys = [c[1] for c in centres]
        x_span = max(xs) - min(xs)
        y_span = max(ys) - min(ys)

        if x_span > y_span * 2.2:
            layout = f"1x{len(centres)}"
        elif y_span > x_span * 2.2:
            layout = f"1x{len(centres)}"
        elif 3 <= len(centres) <= 5:
            layout = "2x2"
        elif 7 <= len(centres) <= 9:
            layout = "2x4"

    return {
        "stud_count": len(centres),
        "stud_layout": layout,
        "stud_centres": [(round(x, 1), round(y, 1)) for x, y in centres],
    }


def recognize_session(processed_session_dir: str) -> dict:
    session_dir = Path(processed_session_dir)
    crops = sorted(session_dir.glob("crop_*.*"))

    if not crops:
        return {"ok": False, "error": "No crop images found", "candidates": []}

    features = [_bbox_features(p) for p in crops]
    ratios = [f["ratio"] for f in features if f["ratio"] > 0]
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0

    stud_runs = [_detect_studs(p) for p in crops]
    best_stud = max(stud_runs, key=lambda x: x["stud_count"], default={"stud_count": 0, "stud_layout": "unknown"})

    candidates = []
    for part in TINY_CATALOG:
        expected_ratio = max(part["stud_x"], part["stud_y"]) / max(1, min(part["stud_x"], part["stud_y"]))
        expected_studs = part["stud_x"] * part["stud_y"]
        expected_layout = f"{min(part['stud_x'], part['stud_y'])}x{max(part['stud_x'], part['stud_y'])}"

        ratio_error = abs(avg_ratio - expected_ratio)
        score = max(0.01, 1.0 - (ratio_error / 4.0))

        # Stud count is stronger than silhouette.
        if best_stud["stud_count"] == expected_studs:
            score += 0.45
        else:
            score -= min(0.45, abs(best_stud["stud_count"] - expected_studs) * 0.12)

        if best_stud["stud_layout"] == expected_layout:
            score += 0.35

        if part["type"] == "brick":
            score += 0.05

        candidates.append({
            "part_num": part["part_num"],
            "name": part["name"],
            "color_id": 0,
            "score": round(max(0.01, min(score, 0.99)), 4),
            "expected_ratio": round(expected_ratio, 3),
            "expected_studs": expected_studs,
            "expected_layout": expected_layout,
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    return {
        "ok": True,
        "session": session_dir.name,
        "photo_count": len(crops),
        "avg_ratio": round(avg_ratio, 4),
        "features": features,
        "stud_detection": stud_runs,
        "best_stud_detection": best_stud,
        "candidates": candidates[:10],
    }

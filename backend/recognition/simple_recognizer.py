from pathlib import Path
from PIL import Image


TINY_CATALOG = [
    {"part_num": "3001", "name": "Brick 2 x 4", "stud_x": 2, "stud_y": 4, "type": "brick"},
    {"part_num": "3010", "name": "Brick 1 x 4", "stud_x": 1, "stud_y": 4, "type": "brick"},
    {"part_num": "3004", "name": "Brick 1 x 2", "stud_x": 1, "stud_y": 2, "type": "brick"},
    {"part_num": "3003", "name": "Brick 2 x 2", "stud_x": 2, "stud_y": 2, "type": "brick"},
    {"part_num": "3039", "name": "Slope 45 2 x 2", "stud_x": 2, "stud_y": 2, "type": "slope"},
    {"part_num": "3040", "name": "Slope 45 2 x 1", "stud_x": 2, "stud_y": 1, "type": "slope"},
]


def _image_features(path: Path) -> dict:
    img = Image.open(path).convert("RGBA")
    bbox = img.getbbox()
    if not bbox:
        return {"width": 0, "height": 0, "ratio": 0}

    l, t, r, b = bbox
    width = max(1, r - l)
    height = max(1, b - t)
    ratio = max(width, height) / max(1, min(width, height))

    return {
        "width": width,
        "height": height,
        "ratio": ratio,
    }


def recognize_session(processed_session_dir: str) -> dict:
    session_dir = Path(processed_session_dir)
    crops = sorted(session_dir.glob("crop_*.*"))

    if not crops:
        return {"ok": False, "error": "No crop images found", "candidates": []}

    features = [_image_features(p) for p in crops]
    ratios = [f["ratio"] for f in features if f["ratio"] > 0]
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0

    # V1 heuristic:
    # A 1x4 brick seen from top/side tends to be long and thin.
    # Score tiny catalog by closeness to stud aspect ratio.
    candidates = []
    for part in TINY_CATALOG:
        expected_ratio = max(part["stud_x"], part["stud_y"]) / max(1, min(part["stud_x"], part["stud_y"]))
        ratio_error = abs(avg_ratio - expected_ratio)
        score = max(0.05, 1.0 - (ratio_error / 4.0))

        if part["type"] == "brick":
            score += 0.08

        candidates.append({
            "part_num": part["part_num"],
            "name": part["name"],
            "color_id": 0,
            "score": round(min(score, 0.99), 4),
            "expected_ratio": expected_ratio,
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    return {
        "ok": True,
        "session": session_dir.name,
        "photo_count": len(crops),
        "avg_ratio": round(avg_ratio, 4),
        "features": features,
        "candidates": candidates[:10],
    }

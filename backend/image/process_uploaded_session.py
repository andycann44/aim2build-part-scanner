from pathlib import Path
from PIL import Image

from backend.image.remove_background import remove_background_file
from backend.image.analysis_images import create_analysis_image, create_analysis_high_image, create_edge_image


def process_session(session_dir: str) -> dict:
    src = Path(session_dir)
    out = Path("backend/processed") / src.name
    out.mkdir(parents=True, exist_ok=True)

    made = []
    image_files = sorted(
        list(src.glob("original_*.jpg")) +
        list(src.glob("original_*.jpeg")) +
        list(src.glob("original_*.png"))
    )

    for img_path in image_files:
        analysis_path = out / img_path.name.replace("original_", "analysis_").rsplit(".", 1)[0]
        analysis_path = analysis_path.with_suffix(".png")

        analysis_high_path = out / img_path.name.replace("original_", "analysis_high_").rsplit(".", 1)[0]
        analysis_high_path = analysis_high_path.with_suffix(".png")

        edge_path = out / img_path.name.replace("original_", "edge_").rsplit(".", 1)[0]
        edge_path = edge_path.with_suffix(".png")

        cutout_path = out / img_path.name.replace("original_", "cutout_").rsplit(".", 1)[0]
        cutout_path = cutout_path.with_suffix(".png")

        create_analysis_image(img_path, analysis_path)
        create_analysis_high_image(img_path, analysis_high_path)
        create_edge_image(analysis_high_path, edge_path)
        remove_background_file(img_path, cutout_path)

        img = Image.open(cutout_path).convert("RGBA")
        bbox = img.getbbox()
        crop = img.crop(bbox) if bbox else img

        crop_path = out / img_path.name.replace("original_", "crop_").rsplit(".", 1)[0]
        crop_path = crop_path.with_suffix(".png")
        thumb_path = out / img_path.name.replace("original_", "thumb_").rsplit(".", 1)[0]
        thumb_path = thumb_path.with_suffix(".png")

        crop.save(crop_path)

        thumb = crop.copy()
        thumb.thumbnail((512, 512))
        thumb.save(thumb_path)

        made.append({
            "original": str(img_path),
            "analysis": str(analysis_path),
            "analysis_high": str(analysis_high_path),
            "edge": str(edge_path),
            "cutout": str(cutout_path),
            "crop": str(crop_path),
            "thumb": str(thumb_path),
        })

    return {"ok": True, "session": src.name, "count": len(made), "files": made}

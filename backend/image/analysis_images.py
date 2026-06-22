from pathlib import Path
from typing import Union

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def create_analysis_image(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path).convert("RGB")

    # Analysis copy only: brighten black LEGO so edges/studs are easier to detect.
    img = ImageEnhance.Brightness(img).enhance(1.8)
    img = ImageEnhance.Contrast(img).enhance(2.2)
    img = ImageEnhance.Sharpness(img).enhance(1.6)

    img.save(output_path)

    return output_path


def create_analysis_high_image(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path).convert("RGB")

    # Second pass for black parts only: expose geometry/studs, not colour truth.
    img = ImageEnhance.Brightness(img).enhance(3.0)
    img = ImageEnhance.Contrast(img).enhance(4.0)
    img = ImageEnhance.Sharpness(img).enhance(2.0)

    img.save(output_path)

    return output_path


def create_edge_image(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path).convert("RGB")
    gray = ImageOps.grayscale(img)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges.save(output_path)

    return output_path

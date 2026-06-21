from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image

ALLOWED_EXTENSIONS = {ext.lower() for ext in Image.registered_extensions()}

# --------------------------------------------------------------------------
# Lossless formats (safe for LSB / robust watermarking)
# --------------------------------------------------------------------------
LOSS_LESS_EXTENSIONS = {".png", ".bmp", ".tiff", ".tif", ".webp"}


def is_lossless_format(ext: str) -> bool:
    """Return True if the extension denotes a lossless image format."""
    return ext.lower() in LOSS_LESS_EXTENSIONS


# --------------------------------------------------------------------------
# Position resolution (shared by text and image watermarks)
# --------------------------------------------------------------------------
def resolve_watermark_position(
    position: Union[Tuple[int, int], str],
    image_size: Tuple[int, int],
    watermark_width: int,
    watermark_height: int,
    margin: int = 10,
) -> Tuple[int, int]:
    """
    Convert a position specification into absolute (x, y) coordinates.

    Supports:
        - tuple (x, y)
        - string "X,Y" (e.g. "100,200")
        - named presets: "bottom-right", "bottom-left", "top-right",
          "top-left", "center"
    """
    if isinstance(position, tuple) and len(position) == 2:
        return position

    if isinstance(position, str):
        # Try to parse explicit "X,Y"
        if "," in position:
            x_str, y_str = position.split(",", 1)
            try:
                return (int(x_str.strip()), int(y_str.strip()))
            except ValueError:
                pass

        w, h = image_size
        pos_lower = position.lower()
        if pos_lower == "bottom-right":
            return (w - watermark_width - margin, h - watermark_height - margin)
        elif pos_lower == "bottom-left":
            return (margin, h - watermark_height - margin)
        elif pos_lower == "top-right":
            return (w - watermark_width - margin, margin)
        elif pos_lower == "top-left":
            return (margin, margin)
        elif pos_lower == "center":
            return ((w - watermark_width) // 2, (h - watermark_height) // 2)
        else:
            return (margin, margin)

    return (margin, margin)


# --------------------------------------------------------------------------
# Existing validation and conversion functions (unchanged)
# --------------------------------------------------------------------------
def is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in ALLOWED_EXTENSIONS


def validate_image(path: Path) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def ensure_valid_image(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    if not is_supported_image(path):
        raise ValueError(
            f"Unsupported image format: {path.suffix}. "
            f"Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    if not validate_image(path):
        raise ValueError(f"Invalid or corrupted image file: {path}")


def ensure_rgb(image_path: Path, output_path: Optional[Path] = None) -> Image.Image:
    with Image.open(image_path) as img:
        if img.mode in ("RGBA", "LA", "P"):
            rgb_img = img.convert("RGB")
        else:
            rgb_img = img.copy()
    if output_path:
        rgb_img.save(output_path)
    return rgb_img

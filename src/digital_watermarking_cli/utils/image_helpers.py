from pathlib import Path
from PIL import Image

ALLOWED_EXTENSIONS = {
    ext.lower()
    for ext in Image.registered_extensions()
}


def is_supported_image(path: Path) -> bool:
    """
    Check whether the file extension is supported by Pillow.
    """
    return path.suffix.lower() in ALLOWED_EXTENSIONS


def ensure_rgb(image_path: Path, output_path: Path | None = None) -> Image.Image:
    """
    Convert an image to RGB if needed.

    Useful when saving to formats that do not support alpha channels,
    such as JPEG.
    """
    img = Image.open(image_path)

    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")

    if output_path:
        img.save(output_path)

    return img
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


def validate_image(path: Path) -> bool:
    """
    Verify that the file is a valid image Pillow can open.
    """
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def ensure_valid_image(path: Path) -> None:
    """
    Validate both the extension and image contents.
    Raises ValueError if validation fails.
    """
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    if not is_supported_image(path):
        raise ValueError(
            f"Unsupported image format: {path.suffix}. "
            f"Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if not validate_image(path):
        raise ValueError(f"Invalid or corrupted image file: {path}")


def ensure_rgb(
    image_path: Path,
    output_path: Path | None = None
) -> Image.Image:
    """
    Convert an image to RGB if needed.

    Useful when saving to formats that do not support alpha channels,
    such as JPEG.
    """
    with Image.open(image_path) as img:
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        else:
            img = img.copy()

    if output_path:
        img.save(output_path)

    return img
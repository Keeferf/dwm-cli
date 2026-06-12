from pathlib import Path
from PIL import Image

ALLOWED_EXTENSIONS = {
    ext.lower()
    for ext in Image.registered_extensions()
}


def is_supported_image(path: Path) -> bool:
    """
    Check whether the file extension is supported by Pillow.

    Returns:
        bool: True if the file extension is in the set of supported extensions.
    """
    return path.suffix.lower() in ALLOWED_EXTENSIONS


def validate_image(path: Path) -> bool:
    """
    Verify that the file is a valid image Pillow can open.

    Returns:
        bool: True if the image can be opened and verified without error.
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

    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the image format is unsupported or the file is corrupted.

    Returns:
        None
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

    Returns:
        Image.Image: The RGB-converted image.
    """
    with Image.open(image_path) as img:
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        else:
            img = img.copy()

    if output_path:
        img.save(output_path)

    return img
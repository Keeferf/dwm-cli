from PIL import Image
from pathlib import Path

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

def is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in ALLOWED_EXTENSIONS

def ensure_rgb(image_path: Path, output_path: Path = None):
    """Convert image to RGB if needed (e.g., for JPEG saving)."""
    img = Image.open(image_path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    if output_path:
        img.save(output_path)
    return img
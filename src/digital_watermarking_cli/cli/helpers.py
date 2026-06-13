"""Configuration and helper utilities."""

from pathlib import Path
from typing import Tuple
from PIL import ImageColor
import importlib.resources as resources

from digital_watermarking_cli.config.settings import load_config, get_current_profile_name
from digital_watermarking_cli.utils.image_helpers import is_supported_image


def get_current_config():
    """Load and return the current configuration."""
    return load_config()


def get_default_font_path() -> str:
    """Get the default Roboto font path from package resources."""
    try:
        with resources.path("digital_watermarking_cli.core", "Roboto-Regular.ttf") as font_path:
            if font_path.exists():
                return str(font_path)
            return ""
    except (ImportError, FileNotFoundError, TypeError):
        return ""


def get_font_display_name(font_path: str) -> str:
    """Get a user-friendly font file name."""
    if not font_path:
        return "Roboto-Regular.ttf (default)"
    return Path(font_path).name


def get_output_dir() -> Path:
    """Get the configured output directory, defaulting to ~/Downloads."""
    config = get_current_config()
    out = config.get("output_dir", "")
    
    if out:
        path = Path(out).expanduser().resolve()
    else:
        path = Path.home() / "Downloads"
    
    path.mkdir(parents=True, exist_ok=True)
    return path


def color_to_rgb(color: str) -> Tuple[int, int, int]:
    """
    Convert a color string to RGB tuple.
    
    Args:
        color: Color name or hex code
    
    Returns:
        (R, G, B) tuple, defaults to white if invalid
    """
    try:
        return ImageColor.getrgb(color)
    except ValueError:
        return (255, 255, 255)


def get_images_from_folder(folder: Path) -> list[Path]:
    """Get all supported image files from a folder."""
    return [p for p in Path(folder).iterdir() if is_supported_image(p)]
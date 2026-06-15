from pathlib import Path
from typing import Tuple

from PIL import ImageColor

from dwm_cli.config.settings import load_config


def get_font_display_name(font_path: str) -> str:
    """Get a user-friendly font file name."""
    if not font_path:
        return "Roboto-Regular.ttf (default)"
    return Path(font_path).name


def get_output_dir() -> Path:
    """Get the configured output directory, defaulting to ~/Downloads."""
    config = load_config()
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
        color: Color name or hex code (e.g., 'red', '#ff0000', '#ff000080')

    Returns:
        (R, G, B) tuple. Alpha channel is ignored if present.
        Defaults to white (255,255,255) on invalid input.
    """
    try:
        rgb = ImageColor.getrgb(color)
        # getrgb may return RGBA (4-tuple); discard alpha if present
        if len(rgb) == 4:
            return rgb[:3]  # type: ignore[return-value]
        return rgb  # type: ignore[return-value]
    except ValueError:
        return (255, 255, 255)

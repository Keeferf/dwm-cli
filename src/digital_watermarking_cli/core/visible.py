from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Tuple, Optional, Union

# Import from utils (sibling of core)
try:
    from ..utils.image_helpers import ensure_valid_image, is_supported_image
except ImportError:
    # Fallback when running as script (if needed)
    from utils.image_helpers import ensure_valid_image, is_supported_image


def _resolve_position(position, image_size, draw, text, font):
    """
    Convert named preset or 'X,Y' string to (x, y) tuple.
    If position is already a tuple, return it unchanged.
    """
    if isinstance(position, tuple) and len(position) == 2:
        return position

    width, height = image_size
    if isinstance(position, str):
        # Try to parse as "X,Y"
        if ',' in position:
            x_str, y_str = position.split(',', 1)
            try:
                return int(x_str.strip()), int(y_str.strip())
            except ValueError:
                pass
        # Named presets
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        margin = 10
        pos_lower = position.lower()
        if pos_lower == "bottom-right":
            return width - text_width - margin, height - text_height - margin
        elif pos_lower == "bottom-left":
            return margin, height - text_height - margin
        elif pos_lower == "top-right":
            return width - text_width - margin, margin
        elif pos_lower == "top-left":
            return margin, margin
        elif pos_lower == "center":
            return (width - text_width) // 2, (height - text_height) // 2
        else:
            # fallback to top-left
            return margin, margin
    # If it's not a string and not a tuple, fallback to (10,10)
    return (10, 10)


def add_text_watermark(
    input_path: Path,
    output_path: Path,
    text: str,
    position: Union[Tuple[int, int], str] = (10, 10),
    font_path: Optional[str] = None,
    font_size: int = 36,
    opacity: float = 0.5,
    text_color: Tuple[int, int, int] = (255, 255, 255),
) -> None:
    """
    Add a visible text watermark to an image.
    Position can be a tuple (x, y) or a string like "bottom-right", "center", etc.
    """
    # Validate input image (exists, supported extension, not corrupted)
    ensure_valid_image(input_path)

    base = Image.open(input_path).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except IOError:
        font = ImageFont.load_default()

    # Resolve position if it's a string preset
    final_position = _resolve_position(position, base.size, draw, text, font)

    alpha = int(255 * opacity)
    color_with_alpha = (*text_color, alpha)
    draw.text(final_position, text, font=font, fill=color_with_alpha)

    watermarked = Image.alpha_composite(base, overlay)
    watermarked_rgb = watermarked.convert("RGB")
    watermarked_rgb.save(output_path, quality=95)


def add_image_watermark(
    input_path: Path,
    output_path: Path,
    watermark_path: Path,
    position: Union[Tuple[int, int], str] = (10, 10),
    scale: float = 1.0,
    opacity: float = 0.5,
) -> None:
    """
    Add an image (logo) watermark.
    Position can be a tuple (x, y) or a string like "bottom-right", "center", etc.
    (For image watermarks, only tuple positions are currently supported;
     if a string is given, it is converted to a simple preset based on image size.)
    """
    # Validate both input image and watermark image
    ensure_valid_image(input_path)
    ensure_valid_image(watermark_path)

    base = Image.open(input_path).convert("RGBA")
    watermark = Image.open(watermark_path).convert("RGBA")

    if scale != 1.0:
        new_size = (int(watermark.width * scale), int(watermark.height * scale))
        watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)

    if opacity < 1.0:
        alpha = watermark.split()[3]
        alpha = alpha.point(lambda p: p * opacity)
        watermark.putalpha(alpha)

    # Resolve position for image watermark (simpler preset handling)
    if isinstance(position, str):
        wm_w, wm_h = watermark.size
        margin = 10
        pos_lower = position.lower()
        if pos_lower == "bottom-right":
            position = (base.width - wm_w - margin, base.height - wm_h - margin)
        elif pos_lower == "bottom-left":
            position = (margin, base.height - wm_h - margin)
        elif pos_lower == "top-right":
            position = (base.width - wm_w - margin, margin)
        elif pos_lower == "top-left":
            position = (margin, margin)
        elif pos_lower == "center":
            position = ((base.width - wm_w) // 2, (base.height - wm_h) // 2)
        else:
            # If not recognised, fallback to (10,10)
            position = (10, 10)

    base.paste(watermark, position, watermark)
    base_rgb = base.convert("RGB")
    base_rgb.save(output_path, quality=95)
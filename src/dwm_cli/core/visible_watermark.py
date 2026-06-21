from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from PIL import Image, ImageDraw, ImageFont

from dwm_cli.utils.image_helpers import resolve_watermark_position

# Font and text‑bbox caches
_FONT_CACHE: Dict[Tuple[Optional[str], int], Any] = {}
_TEXT_BBOX_CACHE: Dict[Tuple[str, Optional[str], int], Tuple[int, int, int, int]] = {}


def _get_cached_font(font_path: Optional[str], font_size: int) -> ImageFont.ImageFont:
    key = (font_path, font_size)
    if key not in _FONT_CACHE:
        try:
            if font_path:
                _FONT_CACHE[key] = ImageFont.truetype(font_path, font_size)
            else:
                _FONT_CACHE[key] = ImageFont.load_default()
        except IOError:
            _FONT_CACHE[key] = ImageFont.load_default()
    return cast(ImageFont.ImageFont, _FONT_CACHE[key])


def _get_text_bbox(
    text: str, font_path: Optional[str], font_size: int
) -> Tuple[int, int, int, int]:
    cache_key = (text, font_path, font_size)
    if cache_key not in _TEXT_BBOX_CACHE:
        font = _get_cached_font(font_path, font_size)
        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        _TEXT_BBOX_CACHE[cache_key] = (
            int(bbox[0]),
            int(bbox[1]),
            int(bbox[2]),
            int(bbox[3]),
        )
    return _TEXT_BBOX_CACHE[cache_key]


def create_text_overlay(
    image_size: Tuple[int, int],
    text: str,
    font_path: Optional[str] = None,
    font_size: int = 36,
    opacity: float = 0.5,
    text_color: Tuple[int, int, int] = (255, 255, 255),
    position: Union[Tuple[int, int], str] = (10, 10),
) -> Image.Image:
    overlay = Image.new("RGBA", image_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _get_cached_font(font_path, font_size)

    bbox = _get_text_bbox(text, font_path, font_size)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    final_position = resolve_watermark_position(
        position, image_size, text_width, text_height
    )

    alpha = int(255 * opacity)
    color_with_alpha = (*text_color, alpha)
    draw.text(final_position, text, font=font, fill=color_with_alpha)
    return overlay


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
    try:
        base: Image.Image = Image.open(input_path)
    except Exception as e:
        raise ValueError(f"Cannot open or read image {input_path}: {e}") from e

    if opacity >= 1.0:
        if base.mode != "RGB":
            base = base.convert("RGB")
        draw = ImageDraw.Draw(base)
        font = _get_cached_font(font_path, font_size)
        bbox = _get_text_bbox(text, font_path, font_size)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        final_position = resolve_watermark_position(
            position, base.size, text_width, text_height
        )
        draw.text(final_position, text, font=font, fill=text_color)
        base.save(output_path, quality=95)
        return

    if base.mode != "RGBA":
        base = base.convert("RGBA")

    overlay = create_text_overlay(
        base.size, text, font_path, font_size, opacity, text_color, position
    )
    watermarked = Image.alpha_composite(base, overlay)
    watermarked.convert("RGB").save(output_path, quality=95)


def _batch_watermark_worker(args):
    inp, out, txt, pos, fp, fs, op, tc = args
    add_text_watermark(inp, out, txt, pos, fp, fs, op, tc)


def add_text_watermark_batch(
    inputs: List[Tuple[Path, Path]],
    text: str,
    position: Union[Tuple[int, int], str] = (10, 10),
    font_path: Optional[str] = None,
    font_size: int = 36,
    opacity: float = 0.5,
    text_color: Tuple[int, int, int] = (255, 255, 255),
    max_workers: Optional[int] = None,
) -> None:
    args_list = [
        (inp, out, text, position, font_path, font_size, opacity, text_color)
        for inp, out in inputs
    ]
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(_batch_watermark_worker, args_list))


def add_image_watermark(
    input_path: Path,
    output_path: Path,
    watermark_path: Path,
    position: Union[Tuple[int, int], str] = (10, 10),
    scale: float = 1.0,
    opacity: float = 0.5,
) -> None:
    try:
        base: Image.Image = Image.open(input_path)
    except Exception as e:
        raise ValueError(f"Cannot open or read image {input_path}: {e}") from e

    try:
        watermark = Image.open(watermark_path).convert("RGBA")
    except Exception as e:
        raise ValueError(
            f"Cannot open or read watermark image {watermark_path}: {e}"
        ) from e

    if scale != 1.0:
        new_size = (int(watermark.width * scale), int(watermark.height * scale))
        watermark = watermark.resize(new_size, Image.Resampling.BICUBIC)

    if opacity < 1.0:
        alpha = watermark.split()[3]
        alpha = alpha.point(lambda p: int(p * opacity))
        watermark.putalpha(alpha)

    final_position = resolve_watermark_position(
        position, base.size, watermark.width, watermark.height
    )

    if base.mode != "RGBA":
        base = base.convert("RGBA")

    base.paste(watermark, final_position, watermark)
    base_rgb = base.convert("RGB")
    base_rgb.save(output_path, quality=95)

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import from the actual module
from dwm_cli.core.visible_watermark import (
    _FONT_CACHE,
    _TEXT_BBOX_CACHE,
    _get_cached_font,
    _get_text_bbox,
    _resolve_position,
    add_image_watermark,
    add_text_watermark,
    add_text_watermark_batch,
    create_text_overlay,
)


# ---------- Fixtures ----------
@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def sample_image_rgb(temp_dir: Path) -> Path:
    img = Image.new("RGB", (200, 150), color=(255, 255, 255))
    path = temp_dir / "input_rgb.jpg"
    img.save(path)
    return path


@pytest.fixture
def sample_image_rgba(temp_dir: Path) -> Path:
    img = Image.new("RGBA", (200, 150), color=(255, 255, 255, 255))
    path = temp_dir / "input_rgba.png"
    img.save(path)
    return path


@pytest.fixture
def watermark_image(temp_dir: Path) -> Path:
    img = Image.new("RGBA", (40, 30), color=(255, 0, 0, 128))
    path = temp_dir / "logo.png"
    img.save(path)
    return path


@pytest.fixture
def output_path(temp_dir: Path) -> Path:
    return temp_dir / "output.jpg"


# ---------- Helper function tests ----------
def test_get_cached_font_default():
    _FONT_CACHE.clear()
    font = _get_cached_font(None, 20)
    assert font is not None
    assert (None, 20) in _FONT_CACHE

    font2 = _get_cached_font("nonexistent.ttf", 20)
    assert font2 is not None


def test_get_cached_font_cache_hit():
    _FONT_CACHE.clear()
    font1 = _get_cached_font(None, 20)
    font2 = _get_cached_font(None, 20)
    assert font1 is font2


def test_get_text_bbox_caching():
    _TEXT_BBOX_CACHE.clear()
    bbox1 = _get_text_bbox("test", None, 20)
    bbox2 = _get_text_bbox("test", None, 20)
    assert bbox1 == bbox2
    assert len(_TEXT_BBOX_CACHE) == 1

    bbox3 = _get_text_bbox("different", None, 20)
    assert bbox3 != bbox1
    assert len(_TEXT_BBOX_CACHE) == 2


def test_resolve_position_tuple():
    pos = _resolve_position((15, 25), (100, 100), "text", None, 20)
    assert pos == (15, 25)


def test_resolve_position_string_xy():
    pos = _resolve_position(" 30 , 40 ", (100, 100), "text", None, 20)
    assert pos == (30, 40)


def test_resolve_position_named_presets():
    with patch("dwm_cli.core.visible_watermark._get_text_bbox") as mock_bbox:
        mock_bbox.return_value = (0, 0, 50, 20)  # width=50, height=20
        width, height = 800, 600
        margin = 10

        pos = _resolve_position("bottom-right", (width, height), "text", None, 20)
        assert pos == (width - 50 - margin, height - 20 - margin)

        pos = _resolve_position("bottom-left", (width, height), "text", None, 20)
        assert pos == (margin, height - 20 - margin)

        pos = _resolve_position("top-right", (width, height), "text", None, 20)
        assert pos == (width - 50 - margin, margin)

        pos = _resolve_position("top-left", (width, height), "text", None, 20)
        assert pos == (margin, margin)

        pos = _resolve_position("center", (width, height), "text", None, 20)
        assert pos == ((width - 50) // 2, (height - 20) // 2)

        pos = _resolve_position("unknown", (width, height), "text", None, 20)
        assert pos == (10, 10)


# ---------- Overlay creation tests ----------
def test_create_text_overlay_basic():
    size = (100, 80)
    overlay = create_text_overlay(size, "Hello", font_size=12, opacity=0.7)
    assert overlay.mode == "RGBA"
    assert overlay.size == size
    alpha_channel = overlay.split()[3]
    alpha_values = list(alpha_channel.getdata())
    assert any(a > 0 for a in alpha_values)


def test_create_text_overlay_position_string():
    size = (300, 200)
    overlay = create_text_overlay(size, "Test", font_size=16, position="bottom-right")
    assert overlay.mode == "RGBA"


# ---------- add_text_watermark tests ----------
def test_add_text_watermark_opaque(sample_image_rgb: Path, output_path: Path):
    add_text_watermark(
        sample_image_rgb,
        output_path,
        "Opaque",
        opacity=1.0,
        text_color=(0, 0, 0),
    )
    assert output_path.exists()
    img = Image.open(output_path)
    assert img.mode == "RGB"


def test_add_text_watermark_transparent(sample_image_rgba: Path, output_path: Path):
    add_text_watermark(
        sample_image_rgba,
        output_path,
        "Transparent",
        opacity=0.5,
    )
    assert output_path.exists()
    img = Image.open(output_path)
    assert img.mode == "RGB"


def test_add_text_watermark_position_string(sample_image_rgb: Path, output_path: Path):
    add_text_watermark(sample_image_rgb, output_path, "Center", position="center")
    assert output_path.exists()


def test_add_text_watermark_invalid_input(temp_dir: Path):
    with pytest.raises(ValueError, match="Cannot open or read image"):
        add_text_watermark(
            temp_dir / "missing.jpg",
            temp_dir / "out.jpg",
            "text",
        )


# ---------- add_image_watermark tests ----------
def test_add_image_watermark_basic(
    sample_image_rgb: Path, watermark_image: Path, output_path: Path
):
    add_image_watermark(
        sample_image_rgb, output_path, watermark_image, scale=0.8, opacity=0.6
    )
    assert output_path.exists()
    img = Image.open(output_path)
    assert img.mode == "RGB"


def test_add_image_watermark_position_string(
    sample_image_rgb: Path, watermark_image: Path, output_path: Path
):
    add_image_watermark(
        sample_image_rgb, output_path, watermark_image, position="bottom-left"
    )
    assert output_path.exists()


def test_add_image_watermark_invalid_watermark(sample_image_rgb: Path, temp_dir: Path):
    with pytest.raises(ValueError, match="Cannot open or read watermark image"):
        add_image_watermark(
            sample_image_rgb, temp_dir / "out.jpg", temp_dir / "missing.png"
        )


# ---------- Batch processing tests ----------
def test_add_text_watermark_batch(sample_image_rgb: Path, temp_dir: Path):
    out1 = temp_dir / "batch1.jpg"
    out2 = temp_dir / "batch2.jpg"
    inputs = [(sample_image_rgb, out1), (sample_image_rgb, out2)]

    add_text_watermark_batch(inputs, "Batch", max_workers=1)
    assert out1.exists()
    assert out2.exists()


def test_batch_worker_error_handling(temp_dir: Path):
    missing = temp_dir / "missing.jpg"
    out = temp_dir / "out.jpg"
    inputs = [(missing, out)]

    with pytest.raises(ValueError, match="Cannot open or read image"):
        add_text_watermark_batch(inputs, "text", max_workers=1)


# ---------- Caching tests ----------
def test_caches_shared_across_calls():
    _FONT_CACHE.clear()
    _TEXT_BBOX_CACHE.clear()

    _get_cached_font(None, 12)
    _get_text_bbox("hello", None, 12)
    assert len(_FONT_CACHE) == 1
    assert len(_TEXT_BBOX_CACHE) == 1

    _get_cached_font(None, 12)
    _get_text_bbox("hello", None, 12)
    assert len(_FONT_CACHE) == 1
    assert len(_TEXT_BBOX_CACHE) == 1


# ---------- Integration test: overlay reuse ----------
def test_create_text_overlay_reuse(sample_image_rgb: Path, temp_dir: Path):
    size = (200, 150)
    overlay = create_text_overlay(size, "Reuse", opacity=0.8)

    img1 = Image.open(sample_image_rgb).convert("RGBA")
    img2 = img1.copy()
    watermarked1 = Image.alpha_composite(img1, overlay)
    watermarked2 = Image.alpha_composite(img2, overlay)

    out1 = temp_dir / "reuse1.jpg"
    out2 = temp_dir / "reuse2.jpg"
    watermarked1.convert("RGB").save(out1)
    watermarked2.convert("RGB").save(out2)

    assert out1.exists()
    assert out2.exists()

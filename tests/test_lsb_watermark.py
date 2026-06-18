# test_lsb_watermark.py
import hashlib  # <-- added for proper RNG seeding in test
import json
import random
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

# ----------------------------------------------------------------------
# Fix import path: add project root (parent of tests/) to sys.path
# ----------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))

# ----------------------------------------------------------------------
# Mock external dependencies (dwm_cli.*) if needed
# ----------------------------------------------------------------------
from dwm_cli.core.lsb_watermark import (  # noqa: E402
    HEADER_BITS,
    MAGIC,
    VERSION,
    NoPayloadError,
    _bits_to_bytes,
    _bytes_to_bits,
    _generate_positions,
    decode_lsb,
    encode_lsb,
)


# ---------- Fixtures ----------
@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def sample_image(temp_dir: Path) -> Path:
    """Create a small RGB image (10x10) and return its path."""
    img_path = temp_dir / "test.png"
    img = Image.new("RGB", (10, 10), color=(128, 128, 128))
    img.save(img_path)
    return img_path


@pytest.fixture
def large_sample_image(temp_dir: Path) -> Path:
    """Create a larger image (100x100) for capacity tests."""
    img_path = temp_dir / "large.png"
    img = Image.new("RGB", (100, 100), color=(0, 0, 0))
    img.save(img_path)
    return img_path


# ----------------------------------------------------------------------
# Helper function tests
# ----------------------------------------------------------------------


def test_bytes_to_bits_roundtrip():
    data = b"Hello"
    bits = _bytes_to_bits(data)
    assert len(bits) == len(data) * 8
    assert _bits_to_bytes(bits) == data

    assert _bytes_to_bits(b"") == []
    assert _bits_to_bytes([]) == b""


def test_bits_to_bytes_requires_multiple_of_8():
    with pytest.raises(ValueError, match="Bit length must be a multiple of 8"):
        _bits_to_bytes([0, 1, 0])


def test_generate_positions_basic():
    rng = random.Random(42)
    positions = _generate_positions(100, 10, rng)
    assert len(positions) == 10
    assert len(set(positions)) == 10
    assert all(0 <= p < 100 for p in positions)


def test_generate_positions_exclude():
    rng = random.Random(42)
    exclude = {0, 1, 2, 3, 4}
    positions = _generate_positions(100, 5, rng, exclude=exclude)
    assert len(positions) == 5
    assert set(positions).isdisjoint(exclude)


def test_generate_positions_insufficient_capacity():
    rng = random.Random(42)
    with pytest.raises(ValueError, match="Not enough capacity"):
        _generate_positions(5, 10, rng)


# ----------------------------------------------------------------------
# Tests for constants
# ----------------------------------------------------------------------


def test_header_bits_constant():
    assert HEADER_BITS == (4 + 1 + 4) * 8


# ----------------------------------------------------------------------
# Encoding / decoding tests (mock console prints)
# ----------------------------------------------------------------------


@patch("dwm_cli.ui.console.console.print")  # suppress warnings
def test_encode_decode_basic(mock_print, sample_image, temp_dir):
    payload = "Hello, world!"
    encoded = encode_lsb(
        sample_image, payload, key="secret", output_path=temp_dir / "out.png"
    )
    assert encoded.exists()

    decoded = decode_lsb(encoded, key="secret")
    assert decoded == payload


@patch("dwm_cli.ui.console.console.print")
def test_encode_with_dict(mock_print, large_sample_image, temp_dir):
    """Use large image to accommodate JSON payload."""
    payload = {"foo": 42, "bar": [1, 2, 3]}
    encoded = encode_lsb(
        large_sample_image, payload, key="key", output_path=temp_dir / "out.png"
    )
    decoded = decode_lsb(encoded, key="key")
    assert json.loads(decoded) == payload


@patch("dwm_cli.ui.console.console.print")
def test_encode_without_key(mock_print, sample_image, temp_dir):
    payload = "no key"
    encoded = encode_lsb(sample_image, payload, output_path=temp_dir / "out.png")
    decoded = decode_lsb(encoded)  # key defaults to ""
    assert decoded == payload


@patch("dwm_cli.ui.console.console.print")
def test_encode_decode_with_different_keys(mock_print, sample_image, temp_dir):
    payload = "confidential"
    encoded = encode_lsb(
        sample_image, payload, key="correct", output_path=temp_dir / "out.png"
    )
    with pytest.raises(NoPayloadError, match="Magic header not found"):
        decode_lsb(encoded, key="wrong")


def test_decode_unwatermarked_image(sample_image):
    with pytest.raises(NoPayloadError, match="Magic header not found"):
        decode_lsb(sample_image, key="any")


@patch("dwm_cli.ui.console.console.print")
def test_payload_too_large(mock_print, sample_image):
    large_payload = "x" * 100  # 10x10 image = 300 bits => ~37 bytes payload max
    with pytest.raises(ValueError, match="Payload too large"):
        encode_lsb(sample_image, large_payload)


def test_invalid_payload_type(sample_image):
    with pytest.raises(TypeError, match="payload must be str or dict"):
        encode_lsb(sample_image, 123)


@patch("dwm_cli.ui.console.console.print")
def test_output_path_autogenerated(mock_print, sample_image, temp_dir):
    encoded = encode_lsb(sample_image, "test", key="k")
    expected_name = sample_image.stem + "_lsb.png"
    assert encoded.name == expected_name
    assert encoded.parent == sample_image.parent


@patch("dwm_cli.ui.console.console.print")
def test_output_path_lossy_format_force_png(mock_print, sample_image, temp_dir):
    out = temp_dir / "out.jpg"
    encoded = encode_lsb(sample_image, "test", key="k", output_path=out)
    assert encoded.suffix == ".png"
    assert encoded.name == "out.png"
    assert not out.exists()


@patch("dwm_cli.ui.console.console.print")
def test_output_path_webp_lossless(mock_print, sample_image, temp_dir):
    out = temp_dir / "out.webp"
    encoded = encode_lsb(sample_image, "test", key="k", output_path=out)
    assert encoded.suffix == ".webp"
    assert encoded.exists()
    with Image.open(encoded) as img:
        assert img.format == "WEBP"


@patch("dwm_cli.ui.console.console.print")
def test_decode_corrupted_or_truncated(mock_print, sample_image, temp_dir):
    payload = "important"
    key = "secret"
    encoded = encode_lsb(
        sample_image, payload, key=key, output_path=temp_dir / "out.png"
    )

    # ------------------------------------------------------------------
    # Determine which pixel bit is actually used for the first embedded bit.
    # Compute the total number of bits embedded (header + payload).
    # ------------------------------------------------------------------
    payload_bytes = payload.encode("utf-8")
    data_bytes = (
        MAGIC
        + VERSION.to_bytes(1, "big")
        + len(payload_bytes).to_bytes(4, "big")
        + payload_bytes
    )
    total_bits = len(data_bytes) * 8

    # Open the encoded image to get its capacity (flattened RGB channels)
    with Image.open(encoded) as img:
        img_rgb = img.convert("RGB")
        pixels = list(img_rgb.getdata())
        flat = []
        for r, g, b in pixels:
            flat.extend([r, g, b])
    capacity = len(flat)

    # Generate the same positions that were used for embedding
    # FIX: use the same seeding as encode_lsb / decode_lsb (SHA‑256)
    seed = int.from_bytes(
        hashlib.sha256(key.encode("utf-8")).digest(),
        byteorder="big",
    )
    rng = random.Random(seed)
    positions = _generate_positions(capacity, total_bits, rng)

    # Flip the LSB at the first used position (this corrupts the magic header)
    first_pos = positions[0]
    flat[first_pos] ^= 1

    # Reconstruct the image and save it
    new_pixels = [(flat[i], flat[i + 1], flat[i + 2]) for i in range(0, len(flat), 3)]
    with Image.open(encoded) as img:
        img.putdata(new_pixels)
        img.save(encoded)

    # Now decoding should fail because the magic header is broken
    with pytest.raises(NoPayloadError, match="Magic header not found"):
        decode_lsb(encoded, key=key)


@patch("dwm_cli.ui.console.console.print")
def test_empty_payload(mock_print, sample_image, temp_dir):
    payload = ""
    encoded = encode_lsb(
        sample_image, payload, key="k", output_path=temp_dir / "out.png"
    )
    decoded = decode_lsb(encoded, key="k")
    assert decoded == ""


@patch("dwm_cli.ui.console.console.print")
def test_large_image_capacity(mock_print, large_sample_image, temp_dir):
    payload = "x" * 3000  # 100x100 image = 30000 bits => ~3750 bytes
    encoded = encode_lsb(
        large_sample_image, payload, key="big", output_path=temp_dir / "out.png"
    )
    decoded = decode_lsb(encoded, key="big")
    assert decoded == payload

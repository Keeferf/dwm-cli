import hashlib
import json
import random
from pathlib import Path
from typing import Optional, Set, Union

from PIL import Image

from dwm_cli.utils.image_helpers import ensure_valid_image


# Custom exception for missing payload
class NoPayloadError(Exception):
    """Raised when no valid LSB payload is found in the image."""

    pass


# Constants for the new payload format
MAGIC = b"DWM1"  # 4 bytes
VERSION = 1  # 1 byte
HEADER_BYTES = 4 + 1 + 4  # magic + version + length = 9 bytes
HEADER_BITS = HEADER_BYTES * 8


def _bytes_to_bits(data: bytes) -> list[int]:
    """Convert bytes to a flat list of bits (MSB first)."""
    bits = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits


def _bits_to_bytes(bits: list[int]) -> bytes:
    """Convert a list of bits back to bytes."""
    if len(bits) % 8 != 0:
        raise ValueError("Bit length must be a multiple of 8")
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        out.append(byte)
    return bytes(out)


def _generate_positions(
    capacity: int,
    num_bits: int,
    rng: random.Random,
    exclude: Optional[Set[int]] = None,
) -> list[int]:
    """
    Generate deterministic pseudo‑random channel positions.

    Args:
        capacity: Total number of available channels (width * height * 3).
        num_bits: Number of positions to generate.
        rng: Seeded random.Random instance.
        exclude: Optional set of indices that must not be chosen.

    Returns:
        List of unique positions of length num_bits.

    Raises:
        ValueError: If capacity is insufficient.
    """
    if exclude:
        population = [i for i in range(capacity) if i not in exclude]
    else:
        population = list(range(capacity))

    if num_bits > len(population):
        raise ValueError(
            f"Not enough capacity: need {num_bits} bits, "
            f"but only {len(population)} available."
        )

    return rng.sample(population, num_bits)


def encode_lsb(
    input_path: Path,
    payload: Union[str, dict],
    key: Optional[str] = None,  # default to None, handled below
    output_path: Optional[Path] = None,
) -> Path:
    """
    Encode a text payload into the LSB of an image using keyed pseudo‑random placement.

    The payload is prefixed with:
        [4‑byte magic] [1‑byte version] [4‑byte length] [payload]

    The same key always produces the same embedding positions.

    Args:
        input_path: Path to the input image.
        payload: String or dict (will be JSON‑encoded).
        key: Secret key used to seed the random placement.
        output_path: Optional output path. If not given, a name is generated.

    Returns:
        Path to the output image.

    Raises:
        ValueError: If the payload is too large for the image.
        TypeError: If payload is not str/dict.
    """
    # If no key is provided, use an empty string (fallback for compatibility)
    if key is None:
        key = ""

    ensure_valid_image(input_path)

    if isinstance(payload, dict):
        payload = json.dumps(payload)
    elif not isinstance(payload, str):
        raise TypeError("payload must be str or dict")

    payload_bytes = payload.encode("utf-8")

    # Build the full data: magic + version + length + payload
    data_bytes = (
        MAGIC
        + VERSION.to_bytes(1, "big")
        + len(payload_bytes).to_bytes(4, "big")
        + payload_bytes
    )
    bits = _bytes_to_bits(data_bytes)
    total_bits = len(bits)

    # Open image and convert to RGB
    with Image.open(input_path) as img:
        img_rgb = img.convert("RGB") if img.mode != "RGB" else img
        pixels = list(img_rgb.getdata())
        flat = []
        for r, g, b in pixels:
            flat.extend([r, g, b])

    capacity = len(flat)

    if total_bits > capacity:
        raise ValueError(
            f"Payload too large: {total_bits} bits needed, "
            f"image provides {capacity} bits."
        )

    # Seed a local RNG from the key
    seed = int.from_bytes(
        hashlib.sha256(key.encode("utf-8")).digest(),
        byteorder="big",
    )
    rng = random.Random(seed)

    # Generate positions: first the fixed‑size header, then the payload
    header_pos = _generate_positions(capacity, HEADER_BITS, rng)
    payload_pos = _generate_positions(
        capacity,
        len(payload_bytes) * 8,
        rng,
        exclude=set(header_pos),
    )
    positions = header_pos + payload_pos  # length == total_bits

    # Embed bits at the chosen positions
    for bit, pos in zip(bits, positions):
        flat[pos] = (flat[pos] & 0xFE) | bit

    # Rebuild image
    new_pixels = []
    for i in range(0, len(flat), 3):
        new_pixels.append(tuple(flat[i : i + 3]))
    img_out = Image.new(img_rgb.mode, img_rgb.size)
    img_out.putdata(new_pixels)

    # ---------- Decide output extension (preserved from original) ----------
    lossless_exts = {".png", ".bmp", ".tiff", ".tif", ".webp"}
    original_ext = input_path.suffix.lower()

    if output_path is None:
        if original_ext in lossless_exts:
            output_ext = original_ext
        else:
            from dwm_cli.ui.console import console

            console.print(
                f"[yellow]⚠ Original format '{original_ext}' is lossy. "
                f"Saving as .png to preserve LSB data.[/]"
            )
            output_ext = ".png"
        output_path = input_path.parent / f"{input_path.stem}_lsb{output_ext}"
    else:
        if output_path.suffix.lower() not in lossless_exts:
            from dwm_cli.ui.console import console

            console.print(
                f"[yellow]⚠ Output format '{output_path.suffix}' may be lossy. "
                f"Forcing .png to protect embedded data.[/]"
            )
            output_path = output_path.with_suffix(".png")

    # Save with appropriate parameters
    if output_path.suffix.lower() == ".webp":
        img_out.save(output_path, lossless=True, quality=100)
    else:
        img_out.save(output_path)

    return output_path


def decode_lsb(
    input_path: Path,
    key: Optional[str] = None,  # default to None, handled below
) -> str:
    """
    Extract the payload from an LSB‑watermarked image using the given key.

    The same key used for encoding must be provided.

    Args:
        input_path: Path to the watermarked image.
        key: Secret key used to generate the embedding positions.

    Returns:
        The extracted payload as a string (JSON if originally a dict).

    Raises:
        NoPayloadError: If the magic header is missing or the key is incorrect.
    """
    if key is None:
        key = ""

    ensure_valid_image(input_path)

    with Image.open(input_path) as img:
        img_rgb = img.convert("RGB") if img.mode != "RGB" else img
        pixels = list(img_rgb.getdata())
        flat = []
        for r, g, b in pixels:
            flat.extend([r, g, b])

    capacity = len(flat)

    # Seed a local RNG from the key
    seed = int.from_bytes(
        hashlib.sha256(key.encode("utf-8")).digest(),
        byteorder="big",
    )
    rng = random.Random(seed)

    # 1. Generate positions for the fixed‑size header (magic, version, length)
    header_pos = _generate_positions(capacity, HEADER_BITS, rng)

    # 2. Extract header bits
    header_bits = [flat[pos] & 1 for pos in header_pos]
    header_bytes = _bits_to_bytes(header_bits)

    # 3. Validate magic and version
    if header_bytes[:4] != MAGIC:
        raise NoPayloadError("Magic header not found – incorrect key or no payload.")
    if header_bytes[4] != VERSION:
        raise NoPayloadError(f"Unsupported version: {header_bytes[4]}")

    # 4. Read payload length (bytes 5..8)
    payload_length = int.from_bytes(header_bytes[5:9], byteorder="big")

    # 5. Generate positions for the payload, excluding the header positions
    payload_bits_count = payload_length * 8
    if capacity < HEADER_BITS + payload_bits_count:
        raise NoPayloadError("Image does not contain enough data for declared payload.")

    payload_pos = _generate_positions(
        capacity,
        payload_bits_count,
        rng,
        exclude=set(header_pos),
    )

    # 6. Extract payload bits
    payload_bits = [flat[pos] & 1 for pos in payload_pos]
    payload_bytes = _bits_to_bytes(payload_bits)

    if len(payload_bytes) != payload_length:
        raise NoPayloadError("Payload length mismatch – data may be corrupted.")

    # 7. Decode and return
    return payload_bytes.decode("utf-8")

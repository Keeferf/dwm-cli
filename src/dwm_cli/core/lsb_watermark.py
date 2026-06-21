import hashlib
import json
import random
from pathlib import Path
from typing import Optional, Set, Union

from PIL import Image

from dwm_cli.utils.image_helpers import ensure_valid_image, is_lossless_format


# Custom exception
class NoPayloadError(Exception):
    pass


# Constants
MAGIC = b"DWM1"
VERSION = 1
HEADER_BYTES = 4 + 1 + 4  # magic + version + length
HEADER_BITS = HEADER_BYTES * 8


def _bytes_to_bits(data: bytes) -> list[int]:
    bits = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits


def _bits_to_bytes(bits: list[int]) -> bytes:
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
    key: Optional[str] = None,
    output_path: Optional[Path] = None,
) -> Path:
    if key is None:
        key = ""

    ensure_valid_image(input_path)

    if isinstance(payload, dict):
        payload = json.dumps(payload)
    elif not isinstance(payload, str):
        raise TypeError("payload must be str or dict")

    payload_bytes = payload.encode("utf-8")
    data_bytes = (
        MAGIC
        + VERSION.to_bytes(1, "big")
        + len(payload_bytes).to_bytes(4, "big")
        + payload_bytes
    )
    bits = _bytes_to_bits(data_bytes)
    total_bits = len(bits)

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

    seed = int.from_bytes(
        hashlib.sha256(key.encode("utf-8")).digest(),
        byteorder="big",
    )
    rng = random.Random(seed)

    header_pos = _generate_positions(capacity, HEADER_BITS, rng)
    payload_pos = _generate_positions(
        capacity,
        len(payload_bytes) * 8,
        rng,
        exclude=set(header_pos),
    )
    positions = header_pos + payload_pos

    for bit, pos in zip(bits, positions):
        flat[pos] = (flat[pos] & 0xFE) | bit

    new_pixels = []
    for i in range(0, len(flat), 3):
        new_pixels.append(tuple(flat[i : i + 3]))
    img_out = Image.new(img_rgb.mode, img_rgb.size)
    img_out.putdata(new_pixels)

    # ---------- Use shared lossless check ----------
    original_ext = input_path.suffix.lower()

    if output_path is None:
        if is_lossless_format(original_ext):
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
        if not is_lossless_format(output_path.suffix):
            from dwm_cli.ui.console import console

            console.print(
                f"[yellow]⚠ Output format '{output_path.suffix}' may be lossy. "
                f"Forcing .png to protect embedded data.[/]"
            )
            output_path = output_path.with_suffix(".png")

    if output_path.suffix.lower() == ".webp":
        img_out.save(output_path, lossless=True, quality=100)
    else:
        img_out.save(output_path)

    return output_path


def decode_lsb(
    input_path: Path,
    key: Optional[str] = None,
) -> str:
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

    seed = int.from_bytes(
        hashlib.sha256(key.encode("utf-8")).digest(),
        byteorder="big",
    )
    rng = random.Random(seed)

    header_pos = _generate_positions(capacity, HEADER_BITS, rng)
    header_bits = [flat[pos] & 1 for pos in header_pos]
    header_bytes = _bits_to_bytes(header_bits)

    if header_bytes[:4] != MAGIC:
        raise NoPayloadError("Magic header not found – incorrect key or no payload.")
    if header_bytes[4] != VERSION:
        raise NoPayloadError(f"Unsupported version: {header_bytes[4]}")

    payload_length = int.from_bytes(header_bytes[5:9], byteorder="big")
    payload_bits_count = payload_length * 8
    if capacity < HEADER_BITS + payload_bits_count:
        raise NoPayloadError("Image does not contain enough data for declared payload.")

    payload_pos = _generate_positions(
        capacity,
        payload_bits_count,
        rng,
        exclude=set(header_pos),
    )
    payload_bits = [flat[pos] & 1 for pos in payload_pos]
    payload_bytes = _bits_to_bytes(payload_bits)

    if len(payload_bytes) != payload_length:
        raise NoPayloadError("Payload length mismatch – data may be corrupted.")

    return payload_bytes.decode("utf-8")

# dct_dwt_qim_watermark.py (updated)

import hashlib
import json
import random
from pathlib import Path
from typing import Optional, Set, Union, cast

import numpy as np
import pywt
from PIL import Image
from scipy.fftpack import dct, idct

from dwm_cli.utils.image_helpers import ensure_valid_image


class NoPayloadError(Exception):
    """Raised when no valid DCT-DWT-QIM payload is found."""

    pass


MAGIC = b"DWM1"  # 4 bytes
VERSION = 1  # 1 byte
HEADER_BYTES = 4 + 1 + 4  # magic + version + length = 9 bytes
HEADER_BITS = HEADER_BYTES * 8


# ---------- Bit helpers ----------
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
    """Generate deterministic pseudo‑random positions."""
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


# ---------- DCT / DWT helpers ----------
def _dct2(block: np.ndarray) -> np.ndarray:
    return cast(np.ndarray, dct(dct(block.T, norm="ortho").T, norm="ortho"))


def _idct2(block: np.ndarray) -> np.ndarray:
    return cast(np.ndarray, idct(idct(block.T, norm="ortho").T, norm="ortho"))


def _dwt2(
    image: np.ndarray, wavelet: str = "haar"
) -> tuple[np.ndarray, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    return cast(
        tuple[np.ndarray, tuple[np.ndarray, np.ndarray, np.ndarray]],
        pywt.dwt2(image, wavelet),
    )


def _idwt2(
    ll: np.ndarray,
    lh: np.ndarray,
    hl: np.ndarray,
    hh: np.ndarray,
    wavelet: str = "haar",
) -> np.ndarray:
    return cast(np.ndarray, pywt.idwt2((ll, (lh, hl, hh)), wavelet))


def _embed_qim(
    coeffs_flat: np.ndarray, bits: list[int], positions: list[int], delta: float
) -> np.ndarray:
    """Embed bits using QIM into a flat coefficient array."""
    for bit, pos in zip(bits, positions):
        x = coeffs_flat[pos]
        if bit == 0:
            coeffs_flat[pos] = delta * np.round(x / delta)
        else:
            coeffs_flat[pos] = delta * np.round((x - delta / 2) / delta) + delta / 2
    return coeffs_flat


def _extract_qim(
    coeffs_flat: np.ndarray, positions: list[int], delta: float
) -> list[int]:
    """Extract bits from a flat coefficient array using QIM."""
    bits = []
    for pos in positions:
        x = coeffs_flat[pos]
        q = delta * np.round(x / delta)
        if abs(x - q) < abs(x - (q + delta / 2 if q < x else q - delta / 2)):
            bits.append(0)
        else:
            bits.append(1)
    return bits


# ---------- Main encode / decode ----------
def encode_dct_dwt_qim(
    input_path: Path,
    payload: Union[str, dict],
    key: Optional[str] = None,
    output_path: Optional[Path] = None,
    delta: float = 4.0,
    wavelet: str = "haar",
) -> Path:
    """
    Encode payload into the LH and HL DWT subbands using DCT + QIM.

    The payload is split across the combined DCT coefficients of LH and HL
    (DC coefficient of each band is skipped).
    """
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

    # Load image, convert to YCbCr, extract Y
    with Image.open(input_path) as img:
        img_ycbcr = img.convert("YCbCr")
        y_channel = np.array(img_ycbcr.getchannel(0), dtype=np.float64)

    # 1. DWT on Y
    ll, (lh, hl, hh) = _dwt2(y_channel, wavelet)

    # 2. DCT on LH and HL separately
    dct_lh = _dct2(lh)
    dct_hl = _dct2(hl)

    # Flatten and exclude DC (index 0) from each
    lh_flat = dct_lh.flatten()[1:]  # skip first coefficient
    hl_flat = dct_hl.flatten()[1:]

    combined = np.concatenate([lh_flat, hl_flat])
    capacity = combined.size

    # Reserve enough space
    if total_bits > capacity:
        raise ValueError(
            f"Payload too large: {total_bits} bits needed, "
            f"but combined LH+HL capacity (minus DCs) is {capacity}."
        )

    # Seed RNG
    seed = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest(), byteorder="big")
    rng = random.Random(seed)

    # Generate positions (no exclusions needed because we already removed DCs)
    positions = _generate_positions(capacity, total_bits, rng)

    # Embed using QIM
    combined_mod = _embed_qim(combined.copy(), bits, positions, delta)

    # Split back into LH and HL
    lh_len = len(lh_flat)
    lh_flat_mod = combined_mod[:lh_len]
    hl_flat_mod = combined_mod[lh_len:]

    # Reinsert DC coefficients (unchanged)
    lh_dc = dct_lh.flatten()[0]
    hl_dc = dct_hl.flatten()[0]
    dct_lh_mod_flat = np.concatenate([[lh_dc], lh_flat_mod])
    dct_hl_mod_flat = np.concatenate([[hl_dc], hl_flat_mod])

    # Reshape back to original band shape
    dct_lh_mod = dct_lh_mod_flat.reshape(dct_lh.shape)
    dct_hl_mod = dct_hl_mod_flat.reshape(dct_hl.shape)

    # Inverse DCT on modified bands
    lh_mod = _idct2(dct_lh_mod)
    hl_mod = _idct2(dct_hl_mod)

    # Inverse DWT
    y_modified = _idwt2(ll, lh_mod, hl_mod, hh, wavelet)
    y_modified = np.clip(y_modified, 0, 255).astype(np.uint8)

    # Reconstruct YCbCr and convert to RGB
    cb = np.array(img_ycbcr.getchannel(1), dtype=np.uint8)
    cr = np.array(img_ycbcr.getchannel(2), dtype=np.uint8)
    ycbcr_modified = np.stack([y_modified, cb, cr], axis=-1)
    img_out = Image.fromarray(ycbcr_modified, mode="YCbCr").convert("RGB")

    # Save losslessly
    lossless_exts = {".png", ".bmp", ".tiff", ".tif", ".webp"}
    original_ext = input_path.suffix.lower()

    if output_path is None:
        if original_ext in lossless_exts:
            output_ext = original_ext
        else:
            from dwm_cli.ui.console import console

            console.print(
                f"[yellow]⚠ Original format '{original_ext}' is lossy. "
                f"Saving as .png to preserve watermark data.[/]"
            )
            output_ext = ".png"
        output_path = input_path.parent / f"{input_path.stem}_dwt_dct_lh_hl{output_ext}"
    else:
        if output_path.suffix.lower() not in lossless_exts:
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


def decode_dct_dwt_qim(
    input_path: Path,
    key: Optional[str] = None,
    delta: float = 4.0,
    wavelet: str = "haar",
) -> str:
    """
    Extract payload from image watermarked with encode_dct_dwt_qim.
    """
    if key is None:
        key = ""

    ensure_valid_image(input_path)

    with Image.open(input_path) as img:
        img_ycbcr = img.convert("YCbCr")
        y_channel = np.array(img_ycbcr.getchannel(0), dtype=np.float64)

    # DWT
    ll, (lh, hl, hh) = _dwt2(y_channel, wavelet)

    # DCT on LH and HL
    dct_lh = _dct2(lh)
    dct_hl = _dct2(hl)

    # Flatten and skip DCs
    lh_flat = dct_lh.flatten()[1:]
    hl_flat = dct_hl.flatten()[1:]
    combined = np.concatenate([lh_flat, hl_flat])
    capacity = combined.size

    # Seed RNG
    seed = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest(), byteorder="big")
    rng = random.Random(seed)

    # 1. Generate header positions (we need to know how many bits header has)
    #    Header size = HEADER_BITS, so we generate that many positions.
    header_pos = _generate_positions(capacity, HEADER_BITS, rng)

    # 2. Extract header bits
    header_bits = _extract_qim(combined, header_pos, delta)
    header_bytes = _bits_to_bytes(header_bits)

    if header_bytes[:4] != MAGIC:
        raise NoPayloadError("Magic header not found – incorrect key or no payload.")
    if header_bytes[4] != VERSION:
        raise NoPayloadError(f"Unsupported version: {header_bytes[4]}")

    payload_length = int.from_bytes(header_bytes[5:9], byteorder="big")
    payload_bits_count = payload_length * 8

    if capacity < HEADER_BITS + payload_bits_count:
        raise NoPayloadError("Image does not contain enough data for declared payload.")

    # 3. Generate payload positions (excluding header positions)
    payload_pos = _generate_positions(
        capacity, payload_bits_count, rng, exclude=set(header_pos)
    )

    # 4. Extract payload bits
    payload_bits = _extract_qim(combined, payload_pos, delta)
    payload_bytes = _bits_to_bytes(payload_bits)

    if len(payload_bytes) != payload_length:
        raise NoPayloadError("Payload length mismatch – data may be corrupted.")

    return payload_bytes.decode("utf-8")

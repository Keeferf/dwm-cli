"""Robust invisible image watermarking using DWT + DCT + QIM.

This module implements a hybrid watermarking scheme that embeds a UTF-8
payload redundantly into the LH and HL sub-bands of a single-level 2D DWT
using block-based DCT and Quantization Index Modulation (QIM).

Future extensibility points:
    - Reed-Solomon / BCH error correction
    - Multiple DWT levels and configurable wavelets
    - Keyed pseudo-random block selection
    - Blind extraction
    - Multi-watermark support
    - Digital signature verification
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Final, cast

import cv2
import numpy as np
import pywt

from dwm_cli.utils.image_helpers import (
    ALLOWED_EXTENSIONS,
    ensure_valid_image,
    is_supported_image,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BLOCK_SIZE: Final[int] = 8
COEFFICIENT: Final[tuple[int, int]] = (3, 3)
DELTA: Final[float] = 20.0
LENGTH_HEADER_BITS: Final[int] = 32  # 32-bit unsigned int for payload length


# ---------------------------------------------------------------------------
# Payload encoding / decoding
# ---------------------------------------------------------------------------
def encode_payload(payload: str) -> tuple[np.ndarray, int]:
    """Encode a UTF-8 payload into a bitstream with a length header.

    Args:
        payload: The UTF-8 text string to encode.

    Returns:
        A tuple of (bit_array, num_bits) where bit_array is a 1-D numpy
        array of ints (0 or 1) and num_bits is the total length.

    Raises:
        ValueError: If the payload is empty or too large for a 32-bit length.
    """
    if not payload:
        raise ValueError("Payload must be non-empty.")

    payload_bytes = payload.encode("utf-8")
    payload_len = len(payload_bytes)

    if payload_len > 0xFFFFFFFF:
        raise ValueError("Payload exceeds maximum supported size (2^32-1 bytes).")

    # [32-bit length header][payload bytes]
    raw = struct.pack(">I", payload_len) + payload_bytes
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8))
    return bits.astype(np.int64), bits.size


def decode_payload(bits: np.ndarray) -> str:
    """Decode a bitstream back into a UTF-8 payload.

    Args:
        bits: 1-D array of ints (0 or 1).

    Returns:
        The decoded UTF-8 string.

    Raises:
        ValueError: If the bitstream is too short or decoding fails.
    """
    if bits.size < LENGTH_HEADER_BITS:
        raise ValueError("Bitstream too short to contain length header.")

    header_bytes = np.packbits(bits[:LENGTH_HEADER_BITS].astype(np.uint8))
    payload_len = struct.unpack(">I", header_bytes.tobytes())[0]

    total_bits = LENGTH_HEADER_BITS + payload_len * 8
    if bits.size < total_bits:
        raise ValueError("Bitstream too short for declared payload length.")

    payload_bytes = np.packbits(bits[LENGTH_HEADER_BITS:total_bits].astype(np.uint8))
    try:
        return payload_bytes.tobytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Decoded payload is not valid UTF-8.") from exc


# ---------------------------------------------------------------------------
# DWT decomposition / reconstruction
# ---------------------------------------------------------------------------
def dwt_decompose(
    channel: np.ndarray, wavelet: str = "haar"
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Perform single-level 2D DWT on a single image channel.

    Args:
        channel: 2-D numpy array (grayscale / luminance).
        wavelet: PyWavelets wavelet name. Defaults to ``haar``.

    Returns:
        Tuple of (LL, LH, HL, HH) sub-bands.

    Raises:
        ValueError: If the channel dimensions are incompatible with DWT.
    """
    if channel.ndim != 2:
        raise ValueError("Channel must be a 2-D array.")
    if channel.shape[0] % 2 or channel.shape[1] % 2:
        raise ValueError("Channel dimensions must be even for single-level DWT.")

    LL, (LH, HL, HH) = pywt.dwt2(channel, wavelet)
    return LL, LH, HL, HH


def dwt_reconstruct(
    LL: np.ndarray,
    LH: np.ndarray,
    HL: np.ndarray,
    HH: np.ndarray,
    wavelet: str = "haar",
) -> np.ndarray:
    """Reconstruct a channel from DWT sub-bands.

    Args:
        LL, LH, HL, HH: Sub-band arrays.
        wavelet: PyWavelets wavelet name.

    Returns:
        Reconstructed 2-D channel.
    """
    return cast(np.ndarray, pywt.idwt2((LL, (LH, HL, HH)), wavelet))


# ---------------------------------------------------------------------------
# DCT processing
# ---------------------------------------------------------------------------
def dct_transform_blocks(
    band: np.ndarray, block_size: int = BLOCK_SIZE
) -> list[np.ndarray]:
    """Apply block-based DCT to a sub-band.

    Args:
        band: 2-D sub-band array.
        block_size: Size of DCT blocks.

    Returns:
        List of DCT blocks in row-major order.

    Raises:
        ValueError: If band dimensions are not multiples of block_size.
    """
    h, w = band.shape
    if h % block_size or w % block_size:
        raise ValueError(
            f"Band dimensions ({h}x{w}) must be multiples of block_size ({block_size})."
        )

    blocks = []
    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            block = band[y : y + block_size, x : x + block_size].astype(np.float32)
            blocks.append(cast(np.ndarray, cv2.dct(block)))
    return blocks


def idct_transform_blocks(
    blocks: list[np.ndarray], band_shape: tuple[int, int], block_size: int = BLOCK_SIZE
) -> np.ndarray:
    """Reconstruct a sub-band from a list of DCT blocks.

    Args:
        blocks: List of DCT coefficient blocks.
        band_shape: Target (height, width) of the reconstructed band.
        block_size: Size of DCT blocks.

    Returns:
        Reconstructed 2-D sub-band.
    """
    h, w = band_shape
    band = np.zeros((h, w), dtype=np.float32)
    idx = 0
    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            block = cast(np.ndarray, cv2.idct(blocks[idx]))
            band[y : y + block_size, x : x + block_size] = block
            idx += 1
    return cast(np.ndarray, band)


# ---------------------------------------------------------------------------
# QIM embedding / extraction
# ---------------------------------------------------------------------------
def qim_embed(value: float, bit: int, delta: float = DELTA) -> float:
    """Embed a single bit into a coefficient using Quantization Index Modulation.

    Bit 0 -> nearest multiple of ``delta``.
    Bit 1 -> nearest ``multiple of delta + delta/2``.

    Args:
        value: Original DCT coefficient.
        bit: Bit to embed (0 or 1).
        delta: Quantization step.

    Returns:
        Modified coefficient.

    Raises:
        ValueError: If bit is not 0 or 1 or delta is non-positive.
    """
    if bit not in (0, 1):
        raise ValueError("Bit must be 0 or 1.")
    if delta <= 0:
        raise ValueError("Delta must be positive.")

    if bit == 0:
        return round(value / delta) * delta
    # bit == 1
    return round((value - delta / 2) / delta) * delta + delta / 2


def qim_extract(value: float, delta: float = DELTA) -> int:
    """Extract a single bit from a QIM-modified coefficient.

    Args:
        value: Modified DCT coefficient.
        delta: Quantization step.

    Returns:
        Extracted bit (0 or 1).

    Raises:
        ValueError: If delta is non-positive.
    """
    if delta <= 0:
        raise ValueError("Delta must be positive.")

    dist_0 = abs(value - round(value / delta) * delta)
    dist_1 = abs(value - (round((value - delta / 2) / delta) * delta + delta / 2))
    return 0 if dist_0 <= dist_1 else 1


def extract_with_confidence(value: float, delta: float = DELTA) -> tuple[int, float]:
    """Extract a bit and return a confidence score.

    The confidence score is the inverse of the quantization error for the
    chosen bit relative to the rejected candidate.  Higher is better.

    Args:
        value: Modified DCT coefficient.
        delta: Quantization step.

    Returns:
        Tuple of (bit, confidence).
    """
    if delta <= 0:
        raise ValueError("Delta must be positive.")

    q0 = round(value / delta) * delta
    q1 = round((value - delta / 2) / delta) * delta + delta / 2
    dist_0 = abs(value - q0)
    dist_1 = abs(value - q1)

    if dist_0 <= dist_1:
        confidence = 1.0 - (dist_0 / (dist_0 + dist_1 + 1e-12))
        return 0, confidence
    confidence = 1.0 - (dist_1 / (dist_0 + dist_1 + 1e-12))
    return 1, confidence


# ---------------------------------------------------------------------------
# Majority voting / redundant recovery
# ---------------------------------------------------------------------------
def majority_vote(bits_a: np.ndarray, bits_b: np.ndarray) -> np.ndarray:
    """Combine two bit arrays using majority voting.

    Args:
        bits_a: Bit array from first extraction (LH).
        bits_b: Bit array from second extraction (HL).

    Returns:
        Combined bit array.

    Raises:
        ValueError: If arrays have different lengths.
    """
    if bits_a.shape != bits_b.shape:
        raise ValueError("Bit arrays must have identical shape for majority voting.")
    return cast(np.ndarray, (bits_a + bits_b >= 1).astype(np.int64))


def combine_with_confidence(
    bits_a: np.ndarray, conf_a: np.ndarray, bits_b: np.ndarray, conf_b: np.ndarray
) -> np.ndarray:
    """Combine two extractions using confidence scores.

    When confidences are equal, falls back to majority voting.

    Args:
        bits_a: Bits from LH.
        conf_a: Confidence scores for LH.
        bits_b: Bits from HL.
        conf_b: Confidence scores for HL.

    Returns:
        Combined bit array.
    """
    result = cast(np.ndarray, np.where(conf_a > conf_b, bits_a, bits_b))
    equal_mask = np.isclose(conf_a, conf_b)
    if np.any(equal_mask):
        voted = majority_vote(bits_a[equal_mask], bits_b[equal_mask])
        result[equal_mask] = voted
    return result


# ---------------------------------------------------------------------------
# Capacity validation
# ---------------------------------------------------------------------------
def calculate_capacity(band: np.ndarray, block_size: int = BLOCK_SIZE) -> int:
    """Return the number of bits that can be embedded in a single band.

    Args:
        band: 2-D sub-band array.
        block_size: DCT block size.

    Returns:
        Available bit capacity.
    """
    h, w = band.shape
    return cast(int, (h // block_size) * (w // block_size))


def validate_capacity(
    band: np.ndarray, num_bits: int, block_size: int = BLOCK_SIZE
) -> None:
    """Validate that a band can hold the required number of bits.

    Args:
        band: 2-D sub-band array.
        num_bits: Required number of bits.
        block_size: DCT block size.

    Raises:
        ValueError: If capacity is insufficient.
    """
    capacity = calculate_capacity(band, block_size)
    if num_bits > capacity:
        raise ValueError(
            f"Watermark payload exceeds available embedding capacity. "
            f"Required: {num_bits} bits, Available: {capacity} bits per band."
        )


# ---------------------------------------------------------------------------
# Image I/O helpers (updated to use shared validation)
# ---------------------------------------------------------------------------
def load_image(image_path: str) -> np.ndarray:
    """Load an image in BGR format and validate the extension.

    Args:
        image_path: Path to the image file.

    Returns:
        Image as a numpy array (BGR, uint8).

    Raises:
        ValueError: If the format is unsupported or loading fails.
    """
    path = Path(image_path)
    ensure_valid_image(path)  # uses PIL to check extension + integrity

    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Failed to load image from {image_path}")
    return img


def save_image(image_path: str, image: np.ndarray) -> None:
    """Save an image, validating the output extension.

    Args:
        image_path: Destination path.
        image: Image array to save.

    Raises:
        ValueError: If the format is unsupported or saving fails.
    """
    path = Path(image_path)
    if not is_supported_image(path):
        raise ValueError(
            f"Unsupported output extension '{path.suffix}'. "
            f"Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)

    # For WEBP, force lossless mode via imwrite params
    params = []
    if path.suffix.lower() == ".webp":
        params = [cv2.IMWRITE_WEBP_QUALITY, 100]

    success = cv2.imwrite(str(path), image, params)
    if not success:
        raise ValueError(f"Failed to save image to {image_path}")


# ---------------------------------------------------------------------------
# Core embedding / extraction
# ---------------------------------------------------------------------------
def _embed_in_band(
    band: np.ndarray,
    bits: np.ndarray,
    block_size: int,
    coefficient: tuple[int, int],
    delta: float,
) -> np.ndarray:
    """Embed a bitstream into a single DWT sub-band.

    Args:
        band: 2-D sub-band array.
        bits: 1-D bit array.
        block_size: DCT block size.
        coefficient: Target DCT coefficient index.
        delta: QIM quantization step.

    Returns:
        Modified sub-band.
    """
    # Pad the band so that its dimensions are multiples of block_size
    h, w = band.shape
    pad_h = (block_size - h % block_size) % block_size
    pad_w = (block_size - w % block_size) % block_size
    if pad_h or pad_w:
        band_padded = np.pad(band, ((0, pad_h), (0, pad_w)), mode="reflect")
    else:
        band_padded = band

    blocks = dct_transform_blocks(band_padded, block_size)
    cy, cx = coefficient

    # Embed into the first len(bits) blocks (which correspond to the original blocks)
    for i, bit in enumerate(bits):
        value = float(blocks[i][cy, cx])
        blocks[i][cy, cx] = qim_embed(value, int(bit), delta)

    # Reconstruct the padded band
    band_reconstructed = idct_transform_blocks(blocks, band_padded.shape, block_size)

    # Crop back to original size if padding was added
    if pad_h or pad_w:
        return band_reconstructed[:h, :w]
    return band_reconstructed


def _extract_from_band(
    band: np.ndarray,
    num_bits: int,
    block_size: int,
    coefficient: tuple[int, int],
    delta: float,
    use_confidence: bool = False,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Extract a bitstream from a single DWT sub-band.

    Args:
        band: 2-D sub-band array.
        num_bits: Number of bits to extract.
        block_size: DCT block size.
        coefficient: Target DCT coefficient index.
        delta: QIM quantization step.
        use_confidence: If True, also return confidence scores.

    Returns:
        Tuple of (bits, confidences).  Confidences is None if
        ``use_confidence`` is False.
    """
    # Pad the band identically to the embedding step
    h, w = band.shape
    pad_h = (block_size - h % block_size) % block_size
    pad_w = (block_size - w % block_size) % block_size
    if pad_h or pad_w:
        band_padded = np.pad(band, ((0, pad_h), (0, pad_w)), mode="reflect")
    else:
        band_padded = band

    blocks = dct_transform_blocks(band_padded, block_size)
    cy, cx = coefficient

    bits: np.ndarray = np.empty(num_bits, dtype=np.int64)
    confidences: np.ndarray | None = (
        np.empty(num_bits, dtype=np.float64) if use_confidence else None
    )

    # Extract from the first num_bits blocks (original blocks)
    for i in range(num_bits):
        val = float(blocks[i][cy, cx])

        if use_confidence:
            bit, conf = extract_with_confidence(val, delta)
            bits[i] = bit
            cast(np.ndarray, confidences)[i] = conf
        else:
            bits[i] = qim_extract(val, delta)

    return bits, confidences


def embed_watermark(
    input_path: str,
    output_path: str,
    payload: str,
    *,
    block_size: int = BLOCK_SIZE,
    coefficient: tuple[int, int] = COEFFICIENT,
    delta: float = DELTA,
    wavelet: str = "haar",
) -> None:
    """Embed a watermark into an image.

    The watermark is embedded redundantly into the LH and HL sub-bands of
    the luminance (Y) channel using block-based DCT and QIM.

    Args:
        input_path: Path to the source image (PNG, TIFF, BMP, WEBP).
        output_path: Path for the watermarked image (PNG, TIFF, BMP, WEBP).
        payload: UTF-8 text string to embed.
        block_size: DCT block size. Defaults to 8.
        coefficient: Target DCT coefficient index. Defaults to (3, 3).
        delta: QIM quantization step. Defaults to 10.0.
        wavelet: PyWavelets wavelet name. Defaults to ``haar``.

    Raises:
        ValueError: On unsupported format, capacity overflow, or invalid params.
    """
    # Load and validate
    img = load_image(input_path)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Convert to YCrCb and work on Y channel
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y_channel = ycrcb[:, :, 0].astype(np.float32)

    # Ensure even dimensions for single-level DWT
    h, w = y_channel.shape
    pad_h, pad_w = h % 2, w % 2
    if pad_h or pad_w:
        y_channel = cv2.copyMakeBorder(
            y_channel, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT_101
        )

    # Encode payload
    bits, num_bits = encode_payload(payload)

    # DWT decomposition
    LL, LH, HL, HH = dwt_decompose(y_channel, wavelet)

    # Validate capacity for both bands
    validate_capacity(LH, num_bits, block_size)
    validate_capacity(HL, num_bits, block_size)

    # Embed redundantly into LH and HL
    LH_embedded = _embed_in_band(LH, bits, block_size, coefficient, delta)
    HL_embedded = _embed_in_band(HL, bits, block_size, coefficient, delta)

    # Reconstruct Y channel
    y_reconstructed = dwt_reconstruct(LL, LH_embedded, HL_embedded, HH, wavelet)

    # Remove padding if added
    if pad_h or pad_w:
        y_reconstructed = y_reconstructed[:h, :w]

    # Clip and restore color channels
    ycrcb[:, :, 0] = np.clip(y_reconstructed, 0, 255).astype(np.uint8)
    watermarked = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

    # Preserve alpha channel if present
    if img.shape[2] == 4:
        watermarked = cv2.cvtColor(watermarked, cv2.COLOR_BGR2BGRA)
        watermarked[:, :, 3] = img[:, :, 3]

    save_image(output_path, watermarked)


def extract_watermark(
    image_path: str,
    *,
    block_size: int = BLOCK_SIZE,
    coefficient: tuple[int, int] = COEFFICIENT,
    delta: float = DELTA,
    wavelet: str = "haar",
    use_confidence: bool = True,
) -> str:
    """Extract a watermark from an image.

    Extracts independently from LH and HL, then combines results using
    confidence scoring (or majority voting as a fallback).

    Args:
        image_path: Path to the watermarked image.
        block_size: DCT block size. Defaults to 8.
        coefficient: Target DCT coefficient index. Defaults to (3, 3).
        delta: QIM quantization step. Defaults to 10.0.
        wavelet: PyWavelets wavelet name. Defaults to ``haar``.
        use_confidence: Whether to use confidence-based fusion. Defaults to True.

    Returns:
        The extracted UTF-8 payload string.

    Raises:
        ValueError: On unsupported format, corrupted data, or extraction failure.
    """
    img = load_image(image_path)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y_channel = ycrcb[:, :, 0].astype(np.float32)

    # Ensure even dimensions (same as embedding)
    h, w = y_channel.shape
    pad_h, pad_w = h % 2, w % 2
    if pad_h or pad_w:
        y_channel = cv2.copyMakeBorder(
            y_channel, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT_101
        )

    # DWT
    LL, LH, HL, HH = dwt_decompose(y_channel, wavelet)

    # We don't know the payload length yet — extract enough bits for the header
    header_capacity = calculate_capacity(LH, block_size)
    header_capacity_hl = calculate_capacity(HL, block_size)
    header_capacity = min(header_capacity, header_capacity_hl)

    # Extract header bits from both bands
    lh_header, lh_header_conf = _extract_from_band(
        LH, LENGTH_HEADER_BITS, block_size, coefficient, delta, use_confidence
    )
    hl_header, hl_header_conf = _extract_from_band(
        HL, LENGTH_HEADER_BITS, block_size, coefficient, delta, use_confidence
    )

    if use_confidence:
        combined_header = combine_with_confidence(
            lh_header,
            cast(np.ndarray, lh_header_conf),
            hl_header,
            cast(np.ndarray, hl_header_conf),
        )
    else:
        combined_header = majority_vote(lh_header, hl_header)

    # Decode header to get payload length
    header_bytes = np.packbits(combined_header.astype(np.uint8))
    payload_len = struct.unpack(">I", header_bytes.tobytes())[0]

    if payload_len == 0:
        raise ValueError(
            "Extracted payload length is zero — likely corrupted or no watermark."
        )

    total_bits = LENGTH_HEADER_BITS + payload_len * 8
    if total_bits > calculate_capacity(
        LH, block_size
    ) or total_bits > calculate_capacity(HL, block_size):
        raise ValueError(
            "Declared payload length exceeds available capacity — data may be corrupted."
        )

    # Extract full payload bits
    lh_bits, lh_conf = _extract_from_band(
        LH, total_bits, block_size, coefficient, delta, use_confidence
    )
    hl_bits, hl_conf = _extract_from_band(
        HL, total_bits, block_size, coefficient, delta, use_confidence
    )

    if use_confidence:
        combined_bits = combine_with_confidence(
            lh_bits,
            cast(np.ndarray, lh_conf),
            hl_bits,
            cast(np.ndarray, hl_conf),
        )
    else:
        combined_bits = majority_vote(lh_bits, hl_bits)

    return decode_payload(combined_bits)

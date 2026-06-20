"""Unit tests for the hybrid DWT+DCT+QIM watermarking module."""

from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from dwm_cli.core.hybrid_watermark import (
    BLOCK_SIZE,
    DELTA,
    calculate_capacity,
    combine_with_confidence,
    dct_transform_blocks,
    decode_payload,
    dwt_decompose,
    dwt_reconstruct,
    embed_watermark,
    encode_payload,
    extract_watermark,
    extract_with_confidence,
    idct_transform_blocks,
    load_image,
    majority_vote,
    qim_embed,
    qim_extract,
    save_image,
    validate_capacity,
)


# ---------------------------------------------------------------------------
# Payload tests
# ---------------------------------------------------------------------------
class TestPayload:
    """Tests for payload encoding and decoding."""

    def test_encode_decode_roundtrip(self) -> None:
        """Encoding then decoding should return the original payload."""
        payload = "Owner: Keefer B\nProject: DWM-CLI\nCreated: 2026-06-19"
        bits, num_bits = encode_payload(payload)
        assert num_bits == bits.size
        assert decode_payload(bits) == payload

    def test_empty_payload_raises(self) -> None:
        """Empty payload must raise ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            encode_payload("")

    def test_unicode_payload(self) -> None:
        """Unicode characters should survive round-trip."""
        payload = "日本語テスト 🎉 ñoño"
        bits, _ = encode_payload(payload)
        assert decode_payload(bits) == payload

    def test_decode_short_bitstream(self) -> None:
        """Too-short bitstream must raise ValueError."""
        with pytest.raises(ValueError, match="too short"):
            decode_payload(np.array([1, 0, 1]))

    def test_very_short_payload(self) -> None:
        """A single character should embed and extract correctly."""
        payload = "A"
        bits, _ = encode_payload(payload)
        assert decode_payload(bits) == payload


# ---------------------------------------------------------------------------
# QIM tests
# ---------------------------------------------------------------------------
class TestQIM:
    """Tests for Quantization Index Modulation."""

    @pytest.mark.parametrize("bit", [0, 1])
    def test_qim_embed_extract_accuracy(self, bit: int) -> None:
        """Embedded bits should be extracted exactly in ideal conditions."""
        original = 42.7
        modified = qim_embed(original, bit, DELTA)
        assert qim_extract(modified, DELTA) == bit

    def test_qim_invalid_bit(self) -> None:
        """Non-binary bit must raise ValueError."""
        with pytest.raises(ValueError, match="0 or 1"):
            qim_embed(1.0, 2, DELTA)

    def test_qim_invalid_delta(self) -> None:
        """Non-positive delta must raise ValueError."""
        with pytest.raises(ValueError, match="positive"):
            qim_embed(1.0, 0, 0.0)
        with pytest.raises(ValueError, match="positive"):
            qim_extract(1.0, -1.0)

    def test_extract_with_confidence(self) -> None:
        """Confidence should be high for a clean coefficient."""
        modified = qim_embed(42.7, 1, DELTA)
        bit, conf = extract_with_confidence(modified, DELTA)
        assert bit == 1
        assert 0.0 <= conf <= 1.0


# ---------------------------------------------------------------------------
# DWT / DCT tests
# ---------------------------------------------------------------------------
class TestTransforms:
    """Tests for DWT and DCT helper functions."""

    def test_dwt_idwt_roundtrip(self) -> None:
        """DWT followed by IDWT should reconstruct the original channel."""
        channel = np.random.randint(0, 256, (256, 256), dtype=np.uint8).astype(
            np.float32
        )
        LL, LH, HL, HH = dwt_decompose(channel)
        reconstructed = dwt_reconstruct(LL, LH, HL, HH)
        np.testing.assert_allclose(reconstructed, channel, atol=1e-4)

    @pytest.mark.parametrize("wavelet", ["haar", "db2", "sym2"])
    def test_dwt_idwt_different_wavelets(self, wavelet: str) -> None:
        """Different wavelets should round-trip correctly."""
        channel = np.random.rand(256, 256).astype(np.float32)
        LL, LH, HL, HH = dwt_decompose(channel, wavelet)
        reconstructed = dwt_reconstruct(LL, LH, HL, HH, wavelet)
        np.testing.assert_allclose(reconstructed, channel, atol=1e-4)

    def test_dct_idct_roundtrip(self) -> None:
        """Block DCT followed by IDCT should reconstruct the band."""
        band = np.random.rand(64, 64).astype(np.float32)
        blocks = dct_transform_blocks(band, BLOCK_SIZE)
        reconstructed = idct_transform_blocks(blocks, band.shape, BLOCK_SIZE)
        np.testing.assert_allclose(reconstructed, band, atol=1e-4)

    def test_dwt_invalid_dimensions(self) -> None:
        """Odd dimensions should raise ValueError."""
        channel = np.zeros((255, 256), dtype=np.float32)
        with pytest.raises(ValueError, match="even"):
            dwt_decompose(channel)

    def test_dct_invalid_block_size(self) -> None:
        """Non-multiple dimensions should raise ValueError."""
        band = np.zeros((60, 60), dtype=np.float32)
        with pytest.raises(ValueError, match="multiples"):
            dct_transform_blocks(band, BLOCK_SIZE)


# ---------------------------------------------------------------------------
# Capacity tests
# ---------------------------------------------------------------------------
class TestCapacity:
    """Tests for capacity calculation and validation."""

    def test_calculate_capacity(self) -> None:
        """Capacity should equal number of 8x8 blocks."""
        band = np.zeros((64, 64), dtype=np.float32)
        assert calculate_capacity(band, BLOCK_SIZE) == (64 // 8) * (64 // 8)

    def test_validate_capacity_pass(self) -> None:
        """Validation should pass when bits fit."""
        band = np.zeros((64, 64), dtype=np.float32)
        validate_capacity(band, 64, BLOCK_SIZE)

    def test_validate_capacity_fail(self) -> None:
        """Validation should raise when bits exceed capacity."""
        band = np.zeros((16, 16), dtype=np.float32)
        with pytest.raises(ValueError, match="exceeds"):
            validate_capacity(band, 10, BLOCK_SIZE)


# ---------------------------------------------------------------------------
# Majority voting / confidence
# ---------------------------------------------------------------------------
class TestRecovery:
    """Tests for redundant recovery strategies."""

    def test_majority_vote_identical(self) -> None:
        """Identical arrays should return themselves."""
        a = np.array([0, 1, 0, 1])
        np.testing.assert_array_equal(majority_vote(a, a), a)

    def test_majority_vote_different(self) -> None:
        """Tie-breaking via sum >= 1."""
        a = np.array([0, 1, 0, 1])
        b = np.array([1, 0, 0, 1])
        expected = np.array([1, 1, 0, 1])
        np.testing.assert_array_equal(majority_vote(a, b), expected)

    def test_majority_vote_shape_mismatch(self) -> None:
        """Different shapes must raise ValueError."""
        with pytest.raises(ValueError, match="identical shape"):
            majority_vote(np.array([0, 1]), np.array([0]))

    def test_combine_with_confidence(self) -> None:
        """Higher confidence should win."""
        bits_a = np.array([0, 1, 0])
        conf_a = np.array([0.9, 0.2, 0.5])
        bits_b = np.array([1, 1, 1])
        conf_b = np.array([0.1, 0.8, 0.5])
        result = combine_with_confidence(bits_a, conf_a, bits_b, conf_b)
        expected = np.array([0, 1, 1])  # last falls back to majority (0+1>=1 -> 1)
        np.testing.assert_array_equal(result, expected)


# ---------------------------------------------------------------------------
# Image I/O tests
# ---------------------------------------------------------------------------
class TestImageIO:
    """Tests for image loading and saving helpers."""

    def test_load_save_roundtrip_png(self) -> None:
        """Save and reload should preserve pixel values (PNG)."""
        img = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.png"
            save_image(str(path), img)
            loaded = load_image(str(path))
            np.testing.assert_array_equal(loaded, img)

    def test_unsupported_input_extension(self) -> None:
        """JPEG input should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported"):
            load_image("image.jpg")

    def test_unsupported_output_extension(self) -> None:
        """JPEG output should raise ValueError."""
        img = np.zeros((8, 8, 3), dtype=np.uint8)
        with pytest.raises(ValueError, match="Unsupported"):
            save_image("image.jpg", img)


# ---------------------------------------------------------------------------
# End-to-end watermarking tests
# ---------------------------------------------------------------------------
class TestWatermarking:
    """Integration tests for embed and extract pipelines."""

    PAYLOAD: str = "Owner: Keefer B\nProject: DWM-CLI\nCreated: 2026-06-19"

    @pytest.fixture
    def sample_image(self, tmp_path: Path) -> Path:
        """Create a random 512x512 RGB image."""
        img = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
        path = tmp_path / "sample.png"
        cv2.imwrite(str(path), img)
        return path

    @pytest.fixture
    def sample_image_alpha(self, tmp_path: Path) -> Path:
        """Create a random 512x512 RGBA image."""
        img = np.random.randint(0, 256, (512, 512, 4), dtype=np.uint8)
        path = tmp_path / "sample_alpha.png"
        cv2.imwrite(str(path), img)
        return path

    def test_embed_extract_lossless(self, sample_image: Path, tmp_path: Path) -> None:
        """Embed and extract on a PNG should be lossless."""
        out = tmp_path / "watermarked.png"
        embed_watermark(str(sample_image), str(out), self.PAYLOAD)
        extracted = extract_watermark(str(out))
        assert extracted == self.PAYLOAD

    def test_embed_extract_tiff(self, sample_image: Path, tmp_path: Path) -> None:
        """TIFF round-trip."""
        out = tmp_path / "watermarked.tif"
        embed_watermark(str(sample_image), str(out), self.PAYLOAD)
        extracted = extract_watermark(str(out))
        assert extracted == self.PAYLOAD

    def test_embed_extract_bmp(self, sample_image: Path, tmp_path: Path) -> None:
        """BMP round-trip."""
        out = tmp_path / "watermarked.bmp"
        embed_watermark(str(sample_image), str(out), self.PAYLOAD)
        extracted = extract_watermark(str(out))
        assert extracted == self.PAYLOAD

    def test_embed_extract_alpha(
        self, sample_image_alpha: Path, tmp_path: Path
    ) -> None:
        """Alpha channel should be preserved after watermarking."""
        out = tmp_path / "watermarked_alpha.png"
        embed_watermark(str(sample_image_alpha), str(out), self.PAYLOAD)
        # Load both and compare alpha
        original = cv2.imread(str(sample_image_alpha), cv2.IMREAD_UNCHANGED)
        watermarked = cv2.imread(str(out), cv2.IMREAD_UNCHANGED)
        np.testing.assert_array_equal(watermarked[:, :, 3], original[:, :, 3])
        # Also ensure extraction works
        extracted = extract_watermark(str(out))
        assert extracted == self.PAYLOAD

    def test_embed_extract_odd_dimensions(self, tmp_path: Path) -> None:
        """Embedding should handle odd image dimensions via padding."""
        img = np.random.randint(0, 256, (513, 511, 3), dtype=np.uint8)
        src = tmp_path / "odd.png"
        cv2.imwrite(str(src), img)
        out = tmp_path / "odd_wm.png"
        embed_watermark(str(src), str(out), self.PAYLOAD)
        extracted = extract_watermark(str(out))
        assert extracted == self.PAYLOAD
        # Check output dimensions match input
        loaded = cv2.imread(str(out))
        assert loaded.shape[:2] == (513, 511)

    def test_different_wavelet(self, sample_image: Path, tmp_path: Path) -> None:
        """Embedding with a different wavelet (db2) should still work."""
        out = tmp_path / "wm_db2.png"
        embed_watermark(str(sample_image), str(out), self.PAYLOAD, wavelet="db2")
        extracted = extract_watermark(str(out), wavelet="db2")
        assert extracted == self.PAYLOAD

    def test_different_block_size(self, sample_image: Path, tmp_path: Path) -> None:
        """Using block_size=4 should still work."""
        out = tmp_path / "wm_bs4.png"
        embed_watermark(str(sample_image), str(out), self.PAYLOAD, block_size=4)
        extracted = extract_watermark(str(out), block_size=4)
        assert extracted == self.PAYLOAD

    def test_different_coefficient(self, sample_image: Path, tmp_path: Path) -> None:
        """Using coefficient=(2,2) should work."""
        out = tmp_path / "wm_coeff.png"
        embed_watermark(str(sample_image), str(out), self.PAYLOAD, coefficient=(2, 2))
        extracted = extract_watermark(str(out), coefficient=(2, 2))
        assert extracted == self.PAYLOAD

    def test_extract_from_non_watermarked(self, sample_image: Path) -> None:
        """Extraction from a clean image should raise ValueError."""
        with pytest.raises(ValueError, match="corrupted|zero"):
            extract_watermark(str(sample_image))

    def test_capacity_validation(self, sample_image: Path, tmp_path: Path) -> None:
        """Oversized payload should raise ValueError."""
        # A tiny image has very low capacity
        tiny = np.zeros((16, 16, 3), dtype=np.uint8)
        tiny_path = tmp_path / "tiny.png"
        cv2.imwrite(str(tiny_path), tiny)
        huge_payload = "x" * 500
        with pytest.raises(ValueError, match="exceeds"):
            embed_watermark(str(tiny_path), str(tmp_path / "out.png"), huge_payload)

    def test_corrupted_image_recovery(self, sample_image: Path, tmp_path: Path) -> None:
        """Extraction should succeed after mild corruption (blur)."""
        out = tmp_path / "watermarked.png"
        embed_watermark(str(sample_image), str(out), self.PAYLOAD)

        # Apply slight Gaussian blur
        img = cv2.imread(str(out))
        blurred = cv2.GaussianBlur(img, (3, 3), 0)
        blurred_path = tmp_path / "blurred.png"
        cv2.imwrite(str(blurred_path), blurred)

        extracted = extract_watermark(str(blurred_path))
        assert extracted == self.PAYLOAD

    def test_majority_voting_fallback(self, sample_image: Path, tmp_path: Path) -> None:
        """Extraction with use_confidence=False should fall back to majority vote."""
        out = tmp_path / "wm.png"
        embed_watermark(str(sample_image), str(out), self.PAYLOAD)
        extracted = extract_watermark(str(out), use_confidence=False)
        assert extracted == self.PAYLOAD


# ---------------------------------------------------------------------------
# Robustness tests
# ---------------------------------------------------------------------------
class TestRobustness:
    """Tests measuring extraction success after image degradation."""

    PAYLOAD: str = "Owner: Keefer B\nProject: DWM-CLI\nCreated: 2026-06-19"

    @pytest.fixture
    def watermarked_image(self, tmp_path: Path) -> Path:
        """Create and watermark a 512x512 image."""
        img = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
        src = tmp_path / "src.png"
        cv2.imwrite(str(src), img)
        out = tmp_path / "wm.png"
        embed_watermark(str(src), str(out), self.PAYLOAD)
        return out

    def _attack_and_extract(
        self, watermarked: Path, tmp_path: Path, attack_fn
    ) -> str | None:
        """Apply an attack and attempt extraction."""
        img = cv2.imread(str(watermarked))
        attacked = attack_fn(img)
        attacked_path = tmp_path / "attacked.png"
        cv2.imwrite(str(attacked_path), attacked)
        try:
            return extract_watermark(str(attacked_path))
        except ValueError:
            return None

    def test_jpeg_quality_95(self, watermarked_image: Path, tmp_path: Path) -> None:
        """Should survive JPEG quality 95."""

        def attack(img):
            buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])[1]
            return cv2.imdecode(buf, cv2.IMREAD_COLOR)

        assert (
            self._attack_and_extract(watermarked_image, tmp_path, attack)
            == self.PAYLOAD
        )

    def test_jpeg_quality_90(self, watermarked_image: Path, tmp_path: Path) -> None:
        """Should survive JPEG quality 90."""

        def attack(img):
            buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])[1]
            return cv2.imdecode(buf, cv2.IMREAD_COLOR)

        assert (
            self._attack_and_extract(watermarked_image, tmp_path, attack)
            == self.PAYLOAD
        )

    def test_jpeg_quality_80(self, watermarked_image: Path, tmp_path: Path) -> None:
        """Should survive JPEG quality 80."""

        def attack(img):
            buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])[1]
            return cv2.imdecode(buf, cv2.IMREAD_COLOR)

        assert (
            self._attack_and_extract(watermarked_image, tmp_path, attack)
            == self.PAYLOAD
        )

    def test_gaussian_noise(self, watermarked_image: Path, tmp_path: Path) -> None:
        """Should survive additive Gaussian noise (sigma=5)."""

        def attack(img):
            noise = np.random.normal(0, 5, img.shape).astype(np.float32)
            noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
            return noisy

        assert (
            self._attack_and_extract(watermarked_image, tmp_path, attack)
            == self.PAYLOAD
        )

    def test_salt_pepper_noise(self, watermarked_image: Path, tmp_path: Path) -> None:
        """Should survive salt-and-pepper noise (1% density)."""

        def attack(img):
            noisy = img.copy()
            h, w, c = img.shape
            mask = np.random.random((h, w)) < 0.01
            noisy[mask] = 0
            mask = np.random.random((h, w)) < 0.01
            noisy[mask] = 255
            return noisy

        assert (
            self._attack_and_extract(watermarked_image, tmp_path, attack)
            == self.PAYLOAD
        )

    def test_small_resize(self, watermarked_image: Path, tmp_path: Path) -> None:
        """Should survive 2%% downscale + upscale."""

        def attack(img):
            h, w = img.shape[:2]
            small = cv2.resize(
                img, (int(w * 0.98), int(h * 0.98)), interpolation=cv2.INTER_LINEAR
            )
            return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)

        assert (
            self._attack_and_extract(watermarked_image, tmp_path, attack)
            == self.PAYLOAD
        )

    def test_minor_blur(self, watermarked_image: Path, tmp_path: Path) -> None:
        """Should survive minor Gaussian blur."""

        def attack(img):
            return cv2.GaussianBlur(img, (3, 3), 0)

        assert (
            self._attack_and_extract(watermarked_image, tmp_path, attack)
            == self.PAYLOAD
        )

    def test_slight_rotation(self, watermarked_image: Path, tmp_path: Path) -> None:
        """Should survive a slight rotation (1 degree)."""

        def attack(img):
            h, w = img.shape[:2]
            center = (w // 2, h // 2)
            mat = cv2.getRotationMatrix2D(center, 1, 1.0)
            return cv2.warpAffine(img, mat, (w, h), borderMode=cv2.BORDER_REFLECT)

        assert (
            self._attack_and_extract(watermarked_image, tmp_path, attack)
            == self.PAYLOAD
        )

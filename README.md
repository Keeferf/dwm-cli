# DWM-CLI: Digital Watermarking Command Line Tool

<div align="center">
<pre>
██████╗ ██╗    ██╗███╗   ███╗      ██████╗██╗     ██╗
██╔══██╗██║    ██║████╗ ████║     ██╔════╝██║     ██║
██║  ██║██║ █╗ ██║██╔████╔██║     ██║     ██║     ██║
██║  ██║██║███╗██║██║╚██╔╝██║     ██║     ██║     ██║
██████╔╝╚███╔███╔╝██║ ╚═╝ ██║     ╚██████╗███████╗██║
╚═════╝  ╚══╝╚══╝ ╚═╝     ╚═╝      ╚═════╝╚══════╝╚═╝
</pre>

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-active-success)]()            
</div>


---

## Overview

**DWM-CLI** is a production-ready command-line tool for digital watermarking with three distinct methods: **visible**, **invisible (LSB)**, and **robust hybrid (DWT+DCT+QIM)**. Built with Python and featuring an intuitive interactive menu system, it enables rapid, batch-friendly watermarking workflows with professional-grade algorithms.

---

## Key Features

### Watermarking Methods

**Visible Watermarking**
- Add professional text or image watermarks to images
- Flexible positioning using preset positions (corners, center) or custom coordinates
- Customizable appearance — control opacity, font size, color, and font selection
- Full-opacity options for opaque watermarks

**Invisible LSB Watermarking**
- Embed encrypted UTF-8 payload into image data using Least Significant Bit (LSB) insertion
- Header-based architecture with payload length tracking
- Keyed extraction — optional passphrase protection for payload recovery
- Capacity: ~1 byte per 3 RGB pixels (lossless formats only)

**Robust Hybrid Watermarking (DWT + DCT + QIM)**
- Military-grade invisible watermark using Discrete Wavelet Transform (DWT), Discrete Cosine Transform (DCT), and Quantization Index Modulation (QIM)
- Redundant embedding across LH and HL wavelet sub-bands for resilience
- Confidence-based extraction with majority voting fallback
- Survives JPEG compression, noise, and minor image alterations
- UTF-8 payload with 32-bit length header

### General Features

- **Interactive Menu System** — User-friendly CLI with guided workflows for seamless operation
- **Batch Processing Ready** — Process multiple images efficiently from the command line
- **Multiple Image Formats** — Support for PNG, JPG, JPEG, TIFF, BMP, and WebP
- **Configuration Management** — Save and reuse watermark settings across sessions
- **Smart Defaults** — Sensible defaults for opacity, positioning, and styling
- **Production-Grade Code** — Type hints, comprehensive docstrings, and extensive test coverage

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Quick Install

```bash
pip install dwm-cli
```

### From Source

```bash
git clone https://github.com/Keeferf/dwm-cli.git
cd dwm-cli
pip install -e .
```

---

## Usage

### Interactive Mode (Recommended)

Launch the interactive menu system:

```bash
dwm-cli
```

---

## Watermarking Methods

### 1. Visible Watermarking

Add visible text or image watermarks to protect copyright and branding.

**Use Cases:**
- Copyright notices on marketing materials
- Logo placement on social media images
- Brand attribution on shared content

**Text Watermark Parameters:**

| Parameter     | Type          | Default         | Description         |
| ------------- | ------------- | --------------- | ------------------- |
| **Text**      | String        | —               | Watermark text      |
| **Position**  | String or XY  | `bottom-right`  | Preset (e.g., "bottom-left") or "X,Y" coords |
| **Font Size** | 1–300+ px     | 36              | Text size in pixels |
| **Opacity**   | 0.0–1.0       | 0.5             | Transparency (0=invisible, 1=opaque) |
| **Color**     | RGB tuple     | (255, 255, 255) | Text color (R, G, B) |
| **Font**      | File path     | Roboto Regular  | Custom TTF font path or system default |

**Preset Positions (5 options):**
- `top-left` — top-left corner (with 10px margin)
- `top-right` — top-right corner (with 10px margin)
- `bottom-left` — bottom-left corner (with 10px margin)
- `bottom-right` — bottom-right corner (with 10px margin)
- `center` — centered on image

Alternatively, use custom coordinates: `"100,50"` (x=100, y=50 from top-left)

**Image Watermark Parameters:**
- Position (presets or XY coordinates)
- Scale factor (1.0 = original size)
- Opacity (0.0–1.0)

---

### 2. Invisible LSB Watermarking

Embed hidden text data into images using Least Significant Bit insertion.

**Use Cases:**
- Covert metadata embedding
- Digital rights management (DRM)
- Hidden author signatures
- Authentication tokens

**Capacity:** ~1 byte per 3 RGB pixels (330 bytes per megapixel)

**Parameters:**

| Parameter    | Type         | Default | Description                 |
| ------------ | ------------ | ------- | --------------------------- |
| **Payload**  | String       | —       | UTF-8 text to embed         |
| **Key**      | String       | (none)  | Optional passphrase         |
| **Format**   | Lossless     | PNG     | Must be lossless (PNG, BMP, TIFF, lossless WebP) |

**Important:** LSB data is destroyed by lossy compression (JPEG). Use only with lossless formats.

**Key-Based Extraction:** If a key is provided during embedding, the same key is required to extract. Incorrect keys will fail extraction.

---

### 3. Robust Hybrid Watermarking (DWT + DCT + QIM)

Embed imperceptible, compression-resistant watermarks using advanced signal processing.

**Use Cases:**
- Broadcast content protection
- Scientific publication authentication
- Medical image watermarking
- Forensic watermark insertion
- Robust copyright marking

**Algorithm:** Discrete Wavelet Transform (Haar) → Block-based DCT → Quantization Index Modulation (QIM)

**Technical Details:**
- Embeds redundantly in LH and HL wavelet sub-bands
- Survives moderate JPEG compression (quality ≥70)
- Resists noise, scaling, and minor alterations
- Confidence-based extraction with fallback majority voting
- 32-bit length header + UTF-8 payload

**Parameters:**

| Parameter      | Type        | Default    | Description              |
| -------------- | ----------- | ---------- | ------------------------ |
| **Payload**    | String      | —          | UTF-8 text to embed      |
| **Block Size** | Int         | 8          | DCT block dimensions     |
| **Coefficient**| (int, int)  | (3, 3)     | Target DCT coefficient   |
| **Delta**      | Float       | 20.0       | QIM quantization step    |
| **Wavelet**    | String      | "haar"     | PyWavelets wavelet name  |

**Recommended Settings:**
- Block size: 8 (standard DCT)
- Coefficient: (3, 3) (good balance of robustness and imperceptibility)
- Delta: 15.0–25.0 (higher = more robust, more visible distortion)

**Capacity:** Payload length depends on image dimensions:
- Example: 512×512 image ≈ 256 bytes capacity
- Example: 1024×1024 image ≈ 1024 bytes capacity

## Configuration

### Watermark Positioning

Watermarks can be positioned using either preset names or custom XY coordinates:

**Preset Positions (5 options):**
- `top-left`
- `top-right`
- `bottom-left`
- `bottom-right`
- `center`

**Custom Coordinates:**
```
100,50            # x=100, y=50 pixels from top-left
```

All presets use a default margin of 10 pixels from edges.

### Method Selection Guide

| Method    | Visibility | Robustness | Capacity | Speed   | Format Requirements |
| --------- | ---------- | ---------- | -------- | ------- | ------------------- |
| Visible   | Yes        | N/A        | High     | Fast    | Any                 |
| LSB       | No         | Low        | Medium   | Medium  | Lossless only       |
| Hybrid    | No         | High       | Low      | Slow    | Any                 |

**Choose Visible** for watermarks meant to be seen (branding, copyright).
**Choose LSB** for covert embedding without compression.
**Choose Hybrid** for robust watermarks that survive JPEG and alterations.

---


## Dependencies

**Core CLI & UI**
- **typer** (≥0.9.0) — CLI framework and command handling
- **rich** — Beautiful terminal formatting and interactive UI components
- **readchar** (≥4.0) — Cross-platform keyboard input

**Image Processing**
- **Pillow** (≥9.0.0) — Image I/O and visible watermarking
- **opencv-python** (≥4.5.0) — Advanced image processing for hybrid watermarking
- **PyWavelets** (≥1.3.0) — Discrete Wavelet Transform (DWT) decomposition
- **numpy** (≥1.20.0) — Numerical operations for DCT and QIM calculations

---

## Platform Support

| OS          | Status          | Notes                       |
| ----------- | --------------- | --------------------------- |
| **macOS**   | ✅ Full Support | Tested on 10.15+            |
| **Linux**   | ✅ Full Support | All distributions           |
| **Windows** | ✅ Full Support | PowerShell & Command Prompt |


## Troubleshooting

### Visible Watermarking

**Issue: Text appears cut off**
- **Cause:** Position coordinates outside image bounds
- **Solution:** Use preset positions (e.g., "bottom-right") or adjust coordinates to fit within image dimensions

**Issue: Custom font not loading**
- **Cause:** Font file path invalid or font file missing
- **Solution:** Use system fonts or ensure the .ttf file path is correct and file exists

**Issue: Text opacity not applying**
- **Cause:** Opacity set to 1.0 (fully opaque)
- **Solution:** Set opacity to < 1.0 for transparency effects; 1.0 produces solid text

### LSB Watermarking

**Issue: "Payload too large"**
- **Cause:** Text exceeds image capacity (~1 byte per 3 RGB pixels)
- **Solution:** Use a smaller payload or larger image

**Issue: Extraction fails or produces garbage**
- **Cause:** Wrong key provided, or image was re-compressed (JPEG)
- **Solution:** Use correct key; ensure image is in lossless format (PNG, BMP, TIFF)

**Issue: "Magic header not found"**
- **Cause:** No LSB watermark in image, or corrupted data
- **Solution:** Verify correct image file and key; ensure embedding succeeded

**Issue: "Output format may be lossy"**
- **Cause:** Attempting to save to lossy format (JPEG)
- **Solution:** Output is automatically converted to PNG; use only lossless formats

### Hybrid Watermarking

**Issue: Extraction returns corrupted payload**
- **Cause:** Image severely compressed or heavily altered
- **Solution:** Use lower JPEG compression (≥70 quality); lower delta (15.0–20.0) for fragility

**Issue: "Payload length exceeds capacity"**
- **Cause:** Text too long for image dimensions
- **Solution:** Reduce payload or use larger image; capacity ≈ (height/2) × (width/2) / 64 bytes

**Issue: Extraction completely fails**
- **Cause:** Wrong block size or coefficient parameters used
- **Solution:** Use default parameters (block_size=8, coefficient=(3,3)); ensure same params for extraction

**Issue: Watermark visible as distortion**
- **Cause:** Delta (QIM step) too high
- **Solution:** Reduce delta to 10.0–15.0; larger deltas increase distortion visibility


## Contributing

Contributions are welcome!

### Development Setup

```bash
git clone https://github.com/Keeferf/dwm-cli.git
cd dwm-cli
pip install -e ".[dev]"
```
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
</div>

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-active-success)]()

---

## Overview

**DWM-CLI** is a production-ready command-line tool for adding professional text watermarks to images. Built with Python and featuring an intuitive interactive menu system, it enables rapid, batch-friendly watermarking workflows.

---

## Key Features

- **Interactive Menu System** — User-friendly CLI with guided workflows for seamless operation
- **Flexible Positioning** — Place watermarks anywhere using preset positions (corners, center) or custom coordinates
- **Customizable Appearance** — Control opacity, font size, color, and font selection
- **Batch Processing Ready** — Process multiple images efficiently from the command line
- **Multiple Image Formats** — Support for PNG, JPG, JPEG, and other common formats
- **Configuration Management** — Save and reuse watermark settings across sessions
- **Smart Defaults** — Sensible defaults for opacity, positioning, and styling
- **Zero External Dependencies** — Lightweight, dependency-conscious design

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

## Configuration

### Watermark Positioning

Watermarks can be positioned using either preset names or custom coordinates:

**Preset Positions:**

```
top-left            top-right
            center
bottom-left         bottom-right
```

**Custom Coordinates:**

```
100,50            # x=100, y=50 pixels from top-left
```

### Watermark Appearance

| Parameter     | Options          | Default         |
| ------------- | ---------------- | --------------- |
| **Text**      | Any string       | —               |
| **Position**  | Presets or "X,Y" | `bottom-right`  |
| **Font Size** | 1–300+ px        | 36              |
| **Opacity**   | 0.0–1.0          | 0.5             |
| **Color**     | RGB tuple        | (255, 255, 255) |
| **Font**      | System TTF files | Default         |

---


## Dependencies

- **typer** (≥0.9.0) — CLI framework and command handling
- **Pillow** (≥9.0.0) — Image processing and rendering
- **readchar** (≥4.0) — Cross-platform keyboard input
- **rich** — Beautiful terminal formatting and interactive UI components

---

## Platform Support

| OS          | Status          | Notes                       |
| ----------- | --------------- | --------------------------- |
| **macOS**   | ✅ Full Support | Tested on 10.15+            |
| **Linux**   | ✅ Full Support | All distributions           |
| **Windows** | ✅ Full Support | PowerShell & Command Prompt |


## Troubleshooting

### Issue: "Image file not supported"

- **Cause:** Corrupted file or unsupported format
- **Solution:** Ensure the image is a valid file and not corrupted

### Issue: Custom font not loading

- **Cause:** Font file path invalid or font file missing
- **Solution:** Use system fonts or ensure the .ttf file path is correct

### Issue: Text appears cut off

- **Cause:** Position coordinates outside image bounds
- **Solution:** Use preset positions (e.g., "bottom-right") or adjust coordinates


## Contributing

Contributions are welcome!

### Development Setup

```bash
git clone https://github.com/Keeferf/dwm-cli.git
cd dwm-cli
pip install -e ".[dev]"
```

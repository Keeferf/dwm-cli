# DWM-CLI: Digital Watermarking Command Line Tool

<div align="center">

```
██████╗ ██╗    ██╗███╗   ███╗      ██████╗██╗     ██╗
██╔══██╗██║    ██║████╗ ████║     ██╔════╝██║     ██║
██║  ██║██║ █╗ ██║██╔████╔██║     ██║     ██║     ██║
██║  ██║██║███╗██║██║╚██╔╝██║     ██║     ██║     ██║
██████╔╝╚███╔███╔╝██║ ╚═╝ ██║     ╚██████╗███████╗██║
╚═════╝  ╚══╝╚══╝ ╚═╝     ╚═╝      ╚═════╝╚══════╝╚═╝
```

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-active-success)]()

</div>

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

This opens a guided interface where you can:

1. Select input image(s)
2. Configure watermark text, position, and styling
3. Customize opacity, font, and color
4. Preview and apply changes

## Configuration

### Watermark Positioning

Watermarks can be positioned using either preset names or custom coordinates:

**Preset Positions:**

```
top-left          top-right
center
bottom-left       bottom-right
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

## Project Structure

```
dwm-cli/
├── src/dwm_cli/
│   ├── cli/                  # Command-line interface
│   │   ├── main.py          # Entry point
│   │   ├── menus/           # Interactive menu system
│   │   ├── prompts/         # User input handlers
│   │   └── helpers.py       # CLI utilities
│   ├── core/                # Core watermarking logic
│   │   └── visible_watermark.py
│   ├── ui/                  # User interface components
│   │   ├── console.py       # Console styling & output
│   │   └── menu_utils.py    # Menu rendering
│   ├── dialogs/             # File selection dialogs
│   ├── config/              # Configuration management
│   ├── utils/               # Utility functions
│   └── assets/              # Fonts & banner artwork
├── pyproject.toml           # Project metadata & dependencies
└── requirements.txt         # Python dependencies
```

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

---

## Troubleshooting

### Issue: "Image file not supported"

- **Cause:** Corrupted file or unsupported format
- **Solution:** Ensure the image is a valid PNG, JPG, or JPEG file and not corrupted

### Issue: Custom font not loading

- **Cause:** Font file path invalid or font file missing
- **Solution:** Use system fonts or ensure the .ttf file path is correct

### Issue: Text appears cut off

- **Cause:** Position coordinates outside image bounds
- **Solution:** Use preset positions (e.g., "bottom-right") or adjust coordinates

### Issue: Watermark too faint

- **Cause:** Opacity too low
- **Solution:** Increase opacity value (range: 0.0–1.0, higher = more visible)

---

## Contributing

Contributions are welcome!

### Development Setup

```bash
git clone https://github.com/Keeferf/dwm-cli.git
cd dwm-cli
pip install -e ".[dev]"
```

---

## Acknowledgments

Built with:

- [Typer](https://typer.tiangolo.com/) — Modern CLI framework
- [Pillow](https://pillow.readthedocs.io/) — Python Imaging Library
- [readchar](https://pypi.org/project/readchar/) — Cross-platform keyboard input
- [Rich](https://rich.readthedocs.io/) — Beautiful terminal formatting and interactive components

---

## Changelog

### v0.1.0 (Initial Release)

- Interactive menu system for watermark application
- Flexible positioning (presets + custom coordinates)
- Customizable opacity, size, color, and fonts
- File selection dialog with multi-file support
- Configuration management system
- Production-ready packaging

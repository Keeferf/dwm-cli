import sys
import time
from pathlib import Path

from rich.console import Group
from rich.text import Text

from dwm_cli.cli.menus.config_menu import manage_configurations
from dwm_cli.cli.menus.help_menu import show_help_menu  # <-- NEW IMPORT
from dwm_cli.cli.prompts.file_prompts import get_input_paths_interactive
from dwm_cli.cli.prompts.hybrid_prompts import (
    process_hybrid_decode_batch,
    process_hybrid_decode_single,
    process_hybrid_encode_batch,
    process_hybrid_encode_single,
)
from dwm_cli.cli.prompts.lsb_prompts import (
    process_lsb_decode_batch,
    process_lsb_decode_single,
    process_lsb_encode_batch,
    process_lsb_encode_single,
)
from dwm_cli.cli.prompts.watermark_prompts import (
    process_image_watermark_batch,
    process_image_watermark_single,
    process_text_watermark_batch,
    process_text_watermark_single,
)
from dwm_cli.ui.console import console, set_global_header
from dwm_cli.ui.menu_utils import interactive_menu


def animated_print(
    text: str, delay: float = 0.001, color_code: str = "\033[38;2;125;122;188m"
) -> None:
    """Print text character by character with ANSI true colour support."""
    sys.stdout.write(color_code)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\033[0m")
    sys.stdout.write("\n")


def build_animated_header() -> Group:
    """Animate the banner, credit line, and GitHub link."""
    banner_path = Path(__file__).parent.parent.parent / "assets" / "banner.txt"
    banner_lines = banner_path.read_text(encoding="utf-8").splitlines()
    max_width = max(len(line) for line in banner_lines)

    top_left = "┌"
    top_right = "┐"
    bottom_left = "└"
    bottom_right = "┘"
    horizontal = "─"
    vertical = "│"
    purple_code = "\033[38;2;125;122;188m"
    reset_code = "\033[0m"

    sys.stdout.write(purple_code)
    sys.stdout.write(f"{top_left}{horizontal * (max_width + 2)}{top_right}\n")
    sys.stdout.write(reset_code)
    sys.stdout.flush()

    for line in banner_lines:
        sys.stdout.write(purple_code)
        sys.stdout.write(f"{vertical} ")
        sys.stdout.flush()
        sys.stdout.write(reset_code)

        sys.stdout.write(purple_code)
        for ch in line:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(0.001)
        sys.stdout.write(reset_code)

        sys.stdout.write(purple_code)
        spaces_needed = max_width - len(line)
        sys.stdout.write(" " * spaces_needed)
        sys.stdout.write(f" {vertical}\n")
        sys.stdout.write(reset_code)
        sys.stdout.flush()

    sys.stdout.write(purple_code)
    sys.stdout.write(f"{bottom_left}{horizontal * (max_width + 2)}{bottom_right}\n")
    sys.stdout.write(reset_code)
    sys.stdout.flush()

    credit = "> Digital Watermarking CLI – Made by Keefer"
    animated_print(credit, delay=0.012, color_code="\033[96m")

    prefix = "> GitHub: "
    sys.stdout.write("\033[96m")
    for ch in prefix:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(0.012)
    sys.stdout.write("\033[0m")
    github_url = "https://github.com/keeferf"
    sys.stdout.write("\033[96m")
    for ch in github_url:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(0.012)
    sys.stdout.write("\033[0m")
    sys.stdout.write("\n")

    banner_text = Text()
    banner_text.append(
        f"{top_left}{horizontal * (max_width + 2)}{top_right}\n",
        style="rgb(125,122,188)",
    )
    for line in banner_lines:
        banner_text.append(
            f"{vertical} {line}{' ' * (max_width - len(line))} {vertical}\n",
            style="rgb(125,122,188)",
        )
    banner_text.append(
        f"{bottom_left}{horizontal * (max_width + 2)}{bottom_right}",
        style="rgb(125,122,188)",
    )

    credit_text = Text(credit, style="cyan")
    github_line = Text("> GitHub: ", style="cyan") + Text(github_url, style="cyan link")

    return Group(banner_text, credit_text, github_line, Text(""))


# ----------------------------------------------------------------------
# Submenus
# ----------------------------------------------------------------------


def show_text_watermark_menu() -> None:
    """Submenu for text watermark options: single or batch."""
    options = ["Single image", "Batch (multiple images)", "Back"]
    while True:
        idx = interactive_menu(options, title="Text Watermark")
        if idx is None or options[idx] == "Back":
            break
        elif idx == 0:  # Single
            paths = get_input_paths_interactive("Select image", mode="single")
            if paths:
                process_text_watermark_single(paths[0])
        elif idx == 1:  # Batch
            paths = get_input_paths_interactive("Select images", mode="multiple")
            if paths:
                process_text_watermark_batch(paths)
        console.clear()


def show_image_watermark_menu() -> None:
    """Submenu for image watermark options: single or batch."""
    options = ["Single image", "Batch (multiple images)", "Back"]
    while True:
        idx = interactive_menu(options, title="Image Watermark")
        if idx is None or options[idx] == "Back":
            break
        elif idx == 0:  # Single
            sources = get_input_paths_interactive("Select source image", mode="single")
            if not sources:
                continue
            watermark = get_input_paths_interactive(
                "Select watermark image (logo)", mode="single"
            )
            if watermark:
                process_image_watermark_single(sources[0], watermark[0])
        elif idx == 1:  # Batch
            sources = get_input_paths_interactive(
                "Select source images", mode="multiple"
            )
            if not sources:
                continue
            watermark = get_input_paths_interactive(
                "Select watermark image (logo)", mode="single"
            )
            if watermark:
                process_image_watermark_batch(sources, watermark[0])
        console.clear()


def show_visible_menu() -> None:
    """Submenu for visible watermarking: text or image."""
    options = ["Text watermark", "Image watermark", "Back"]
    while True:
        idx = interactive_menu(options, title="Visible Watermarking")
        if idx is None or options[idx] == "Back":
            break
        elif idx == 0:
            show_text_watermark_menu()
        elif idx == 1:
            show_image_watermark_menu()
        console.clear()


# ----------------------------------------------------------------------
# LSB Submenu with Batch Decode
# ----------------------------------------------------------------------


def show_lsb_menu() -> None:
    """Submenu for LSB steganography: encode or decode."""
    options = [
        "Encode (single image)",
        "Encode (batch multiple)",
        "Decode (single image)",
        "Decode (batch multiple)",
        "Back",
    ]
    while True:
        idx = interactive_menu(options, title="LSB Steganography")
        if idx is None or options[idx] == "Back":
            break
        elif idx == 0:  # Encode single
            paths = get_input_paths_interactive("Select image", mode="single")
            if paths:
                process_lsb_encode_single(paths[0])
        elif idx == 1:  # Encode batch
            paths = get_input_paths_interactive("Select images", mode="multiple")
            if paths:
                process_lsb_encode_batch(paths)
        elif idx == 2:  # Decode single
            paths = get_input_paths_interactive(
                "Select LSB-watermarked image", mode="single"
            )
            if paths:
                process_lsb_decode_single(paths[0])
        elif idx == 3:  # Decode batch
            paths = get_input_paths_interactive(
                "Select LSB-watermarked images", mode="multiple"
            )
            if paths:
                process_lsb_decode_batch(paths)
        console.clear()


# ----------------------------------------------------------------------
# Hybrid Submenu (was Multi‑Domain)
# ----------------------------------------------------------------------


def show_hybrid_menu() -> None:
    """Submenu for DCT-DWT-QIM watermarking: encode or decode."""
    options = [
        "Encode (single image)",
        "Encode (batch multiple)",
        "Decode (single image)",
        "Decode (batch multiple)",
        "Back",
    ]
    while True:
        idx = interactive_menu(options, title="Hybrid Watermarking")
        if idx is None or options[idx] == "Back":
            break
        elif idx == 0:  # Encode single
            paths = get_input_paths_interactive("Select image", mode="single")
            if paths:
                process_hybrid_encode_single(paths[0])
        elif idx == 1:  # Encode batch
            paths = get_input_paths_interactive("Select images", mode="multiple")
            if paths:
                process_hybrid_encode_batch(paths)
        elif idx == 2:  # Decode single
            paths = get_input_paths_interactive(
                "Select watermarked image", mode="single"
            )
            if paths:
                process_hybrid_decode_single(paths[0])
        elif idx == 3:  # Decode batch
            paths = get_input_paths_interactive(
                "Select watermarked images", mode="multiple"
            )
            if paths:
                process_hybrid_decode_batch(paths)
        console.clear()


# ----------------------------------------------------------------------
# Main menu
# ----------------------------------------------------------------------


def show_main_menu() -> None:
    """Display and handle the main menu with animated header."""
    persistent_header = build_animated_header()
    set_global_header(persistent_header)

    menu_actions = {
        "Visible Watermarking": show_visible_menu,
        "LSB Watermarking": show_lsb_menu,
        "Hybrid Watermarking": show_hybrid_menu,
        "Manage configurations": manage_configurations,
        "Help / Explain": show_help_menu,  # <-- NEW ENTRY (replaces "More features")
        "Exit": lambda: True,
    }
    options = list(menu_actions.keys())

    while True:
        idx = interactive_menu(options, title="Main Menu")
        if idx is None:
            break

        action = menu_actions[options[idx]]
        if action is menu_actions["Exit"]:
            console.clear()
            break
        else:
            console.clear()
            action()

import sys
import time
from pathlib import Path

from rich.console import Group
from rich.text import Text

from dwm_cli.cli.menus.config_menu import manage_configurations
from dwm_cli.cli.prompts.file_prompts import (
    get_images_from_folder_prompt,
    prompt_for_folder,
    prompt_for_multiple_files,
    prompt_for_single_file,
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
    """
    Print text character by character with ANSI true colour support.

    Args:
        text: The string to print with animation.
        delay: Time in seconds between printing each character.
        color_code: ANSI escape sequence for the text colour.
    """
    sys.stdout.write(color_code)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\033[0m")
    sys.stdout.write("\n")


def build_animated_header() -> Group:
    """
    Animate the banner, credit line, and GitHub link.

    Returns:
        Group: A Rich Group containing the animated header elements.
    """
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
    """Submenu for text watermark options: single, batch multiple, batch folder."""
    options = [
        "Single image",
        "Batch (multiple images)",
        "Batch (folder)",
        "Back",
    ]
    while True:
        idx = interactive_menu(options, title="Text Watermark")
        if idx is None or options[idx] == "Back":
            break
        elif idx == 0:  # Single
            path = prompt_for_single_file("an image")
            if path:
                process_text_watermark_single(path)
        elif idx == 1:  # Batch multiple
            paths = prompt_for_multiple_files("images")
            if paths:
                process_text_watermark_batch(paths)
        elif idx == 2:  # Batch folder
            folder = prompt_for_folder()
            if folder:
                images = get_images_from_folder_prompt(folder)
                if images:
                    process_text_watermark_batch(images)
        console.clear()  # Clear after action returns to submenu


def show_image_watermark_menu() -> None:
    """Submenu for image watermark options: single, batch multiple, batch folder."""
    options = [
        "Single image",
        "Batch (multiple images)",
        "Batch (folder)",
        "Back",
    ]
    while True:
        idx = interactive_menu(options, title="Image Watermark")
        if idx is None or options[idx] == "Back":
            break
        elif idx == 0:  # Single
            source = prompt_for_single_file("source image")
            if not source:
                continue
            watermark = prompt_for_single_file("watermark image (logo)")
            if watermark:
                process_image_watermark_single(source, watermark)
        elif idx == 1:  # Batch multiple
            sources = prompt_for_multiple_files("source images")
            if not sources:
                continue
            watermark = prompt_for_single_file("watermark image (logo)")
            if watermark:
                process_image_watermark_batch(sources, watermark)
        elif idx == 2:  # Batch folder
            folder = prompt_for_folder()
            if not folder:
                continue
            sources = get_images_from_folder_prompt(folder)
            if not sources:
                continue
            watermark = prompt_for_single_file("watermark image (logo)")
            if watermark:
                process_image_watermark_batch(sources, watermark)
        console.clear()


def show_visible_menu() -> None:
    """Submenu for visible watermarking: text or image."""
    options = ["Text watermark", "Image watermark", "Back"]
    while True:
        idx = interactive_menu(options, title="Visible Watermarking")
        if idx is None or options[idx] == "Back":
            break
        elif idx == 0:  # Text
            show_text_watermark_menu()
        elif idx == 1:  # Image
            show_image_watermark_menu()
        console.clear()


def show_more_features_menu() -> None:
    """Placeholder for future encoding models (invisible watermarking)."""
    options = ["Encoding models (coming soon)", "Back"]
    while True:
        idx = interactive_menu(options, title="More Features")
        if idx is None or options[idx] == "Back":
            break
        elif idx == 0:
            from dwm_cli.ui.console import wait_for_enter

            console.print(
                "[italic cyan]Invisible watermarking & encoding models are under development![/]"
            )
            wait_for_enter()
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
        "Manage configurations": manage_configurations,
        "More features (encoding models)": show_more_features_menu,
        "Exit": lambda: True,
    }
    options = list(menu_actions.keys())

    while True:
        idx = interactive_menu(options, title="Main Menu")
        if idx is None:  # Esc/q pressed
            break

        action = menu_actions[options[idx]]
        if action is menu_actions["Exit"]:
            console.clear()
            break
        else:
            console.clear()
            action()

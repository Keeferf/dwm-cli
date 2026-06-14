import sys
import time
from pathlib import Path

from rich.prompt import Prompt
from rich.console import Group
from rich.text import Text

from dwm_cli.ui.console import console, set_global_header
from dwm_cli.ui.menu_utils import interactive_menu
from dwm_cli.cli.prompts.file_prompts import get_input_paths_interactive
from dwm_cli.cli.prompts.watermark_prompts import (
    prompt_text_watermark,
    prompt_image_watermark,
    prompt_text_watermark_batch,
    prompt_image_watermark_batch
)
from dwm_cli.cli.menus.config_menu import manage_configurations


def animated_print(text: str, delay: float = 0.001, color_code: str = "\033[38;2;125;122;188m") -> None:
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
    banner_text.append(f"{top_left}{horizontal * (max_width + 2)}{top_right}\n", style="rgb(125,122,188)")
    for line in banner_lines:
        banner_text.append(f"{vertical} {line}{' ' * (max_width - len(line))} {vertical}\n", style="rgb(125,122,188)")
    banner_text.append(f"{bottom_left}{horizontal * (max_width + 2)}{bottom_right}", style="rgb(125,122,188)")

    credit_text = Text(credit, style="cyan")
    github_line = Text("> GitHub: ", style="cyan") + Text(github_url, style="cyan link")

    return Group(banner_text, credit_text, github_line, Text(""))


def show_main_menu() -> None:
    """Display and handle the main menu with animated header and keyboard navigation."""
    persistent_header = build_animated_header()
    set_global_header(persistent_header)

    def action_text_watermark():
        """Prompt user for text watermark parameters and apply to a single image."""
        prompt_text_watermark()
        Prompt.ask("\nPress Enter to continue", default="")

    def action_image_watermark():
        """Prompt user for image watermark parameters and apply to a single image."""
        prompt_image_watermark()
        Prompt.ask("\nPress Enter to continue", default="")

    def action_batch_text():
        """Prompt user for text watermark parameters and apply to multiple images."""
        inputs = get_input_paths_interactive(
            "Select images for batch text watermark",
            [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        prompt_text_watermark_batch(inputs)
        Prompt.ask("\nPress Enter to continue", default="")

    def action_batch_image():
        """Prompt user for image watermark parameters and apply to multiple images."""
        inputs = get_input_paths_interactive(
            "Select images for batch image watermark",
            [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        prompt_image_watermark_batch(inputs)
        Prompt.ask("\nPress Enter to continue", default="")

    def action_manage_configs():
        """Open the configuration management submenu."""
        manage_configurations()

    def action_exit():
        """Exit the application.

        Returns:
            bool: True to indicate exit.
        """
        console.print("[bold green]Goodbye![/]")
        return True

    # Dictionary mapping menu labels to action functions
    menu_actions = {
        "Text watermark (single image)": action_text_watermark,
        "Image watermark (single image)": action_image_watermark,
        "Batch text watermark (multiple images/folder)": action_batch_text,
        "Batch image watermark (multiple images/folder)": action_batch_image,
        "Manage configurations (profiles)": action_manage_configs,
        "Exit": action_exit,
    }
    options = list(menu_actions.keys())

    while True:
        idx = interactive_menu(options, title="Main Menu")
        if idx is None:      # User pressed Esc/q
            break

        action = menu_actions[options[idx]]
        if action is action_exit:
            if action():
                break
        else:
            console.clear()
            action()
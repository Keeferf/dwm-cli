"""Main menu and navigation for the watermarking CLI."""

import sys
import time
from functools import partial

from rich.prompt import Prompt
from rich.panel import Panel

from dwm_cli.ui.console import console, clear_screen
from dwm_cli.cli.prompts.file_prompts import get_input_paths_interactive
from dwm_cli.cli.prompts.watermark_prompts import (
    prompt_text_watermark,
    prompt_image_watermark,
    prompt_text_watermark_batch,
    prompt_image_watermark_batch
)
from dwm_cli.cli.menus.config_menu import manage_configurations


def animated_print(text: str, delay: float = 0.001, color_code: str = "\033[38;2;125;122;188m") -> None:
    """Print text character by character with ANSI true‑colour support."""
    sys.stdout.write(color_code)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\033[0m")
    sys.stdout.write("\n")


def display_header() -> None:
    """Display a static purple border with an animated DWM CLI banner inside."""
    clear_screen()

    # Banner – safe UTF‑8 block characters
    banner_lines = [
        "██████╗ ██╗    ██╗███╗   ███╗       ██████╗██╗     ██╗",
        "██╔══██╗██║    ██║████╗ ████║      ██╔════╝██║     ██║",
        "██║  ██║██║ █╗ ██║██╔████╔██║█████╗██║     ██║     ██║",
        "██║  ██║██║███╗██║██║╚██╔╝██║╚════╝██║     ██║     ██║",
        "██████╔╝╚███╔███╔╝██║ ╚═╝ ██║      ╚██████╗███████╗██║",
        "╚═════╝  ╚══╝╚══╝ ╚═╝     ╚═╝       ╚═════╝╚══════╝╚═╝",
    ]

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
    console.print(f"[cyan][link={github_url}]{github_url}[/link][/cyan]")
    console.print()


def show_main_menu() -> None:
    """Display and handle the main menu loop using a dictionary action map."""
    display_header()

    # ----- Action functions (each returns True to exit, False to stay) -----
    def action_text_watermark():
        prompt_text_watermark()
        Prompt.ask("\nPress Enter to continue", default="")
        clear_screen()
        return False

    def action_image_watermark():
        prompt_image_watermark()
        Prompt.ask("\nPress Enter to continue", default="")
        clear_screen()
        return False

    def action_batch_text():
        inputs = get_input_paths_interactive(
            "Select images for batch text watermark",
            [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        prompt_text_watermark_batch(inputs)
        Prompt.ask("\nPress Enter to continue", default="")
        clear_screen()
        return False

    def action_batch_image():
        inputs = get_input_paths_interactive(
            "Select images for batch image watermark",
            [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        prompt_image_watermark_batch(inputs)
        Prompt.ask("\nPress Enter to continue", default="")
        clear_screen()
        return False

    def action_manage_configs():
        manage_configurations()
        clear_screen()
        return False

    def action_exit():
        console.print("[bold green]Goodbye![/]")
        return True

    # Map option keys to their action functions
    menu_actions = {
        "1": action_text_watermark,
        "2": action_image_watermark,
        "3": action_batch_text,
        "4": action_batch_image,
        "5": action_manage_configs,
        "6": action_exit,
    }

    while True:
        menu_options = (
            "1. Text watermark (single image)\n"
            "2. Image watermark (single image)\n"
            "3. Batch text watermark (multiple images/folder)\n"
            "4. Batch image watermark (multiple images/folder)\n"
            "5. Manage configurations (profiles)\n"
            "6. Exit"
        )
        console.print(Panel(menu_options, title="Main Menu", border_style="blue"))
        choice = Prompt.ask("Select option", choices=list(menu_actions.keys()), default="6")

        action = menu_actions.get(choice)
        if action:
            should_exit = action()
            if should_exit:
                break
        else:
            console.print("[red]Invalid choice, try again.[/]")
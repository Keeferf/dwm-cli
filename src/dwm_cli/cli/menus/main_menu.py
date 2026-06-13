"""Main menu and navigation for the watermarking CLI."""

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


def display_header() -> None:
    """Display the application header with ASCII art."""
    clear_screen()
    
    ascii_art = r"""
    ██ ██▓▒    ██▒▓███   ███      ██████▓▒     ██▒ 
    ██▒▓▒▒██▒██▓    ██▒█████ ████▒     ██▒▓▒▒▒▒▒▓██▒     ██▒ 
    ██▒  ██▒██▒ ██▓ ██▒██▒███▒██▒     ██▒     ██▒     ██▒ 
    ██▒  ██▒██▒███▓██▒██▒▒██▒▒▓██▒     ██▒     ██▒     ██▒ 
    ██████▒▓▒▒▒███▒██▒███▒▒▓██▒ ██▒    ██▒     ▓██████▓██████▓██▒ 
    ▓▒▒▒▒▒▒▒  ▓▒▒▒▒▒▒▒ ▒▒▒▒     ▒▒▒      ▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ 
    """
    console.print(Panel(ascii_art, style="purple", expand=False))
    
    github_url = "https://github.com/keeferf"
    console.print("[dim]Made by: Keefer[/]")
    console.print(f"[dim]My Github: [link={github_url}]{github_url}[/link][/dim]")
    console.print()


def show_main_menu() -> None:
    """Display and handle the main menu loop."""
    display_header()
    
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
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6"], default="6")

        if choice == "1":
            prompt_text_watermark()
            Prompt.ask("\nPress Enter to continue", default="")
            clear_screen()
        
        elif choice == "2":
            prompt_image_watermark()
            Prompt.ask("\nPress Enter to continue", default="")
            clear_screen()
        
        elif choice == "3":
            inputs = get_input_paths_interactive(
                "Select images for batch text watermark",
                [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
            )
            prompt_text_watermark_batch(inputs)
            Prompt.ask("\nPress Enter to continue", default="")
            clear_screen()
        
        elif choice == "4":
            inputs = get_input_paths_interactive(
                "Select images for batch image watermark",
                [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
            )
            prompt_image_watermark_batch(inputs)
            Prompt.ask("\nPress Enter to continue", default="")
            clear_screen()
        
        elif choice == "5":
            manage_configurations()
            clear_screen()
        
        elif choice == "6":
            console.print("[bold green]Goodbye![/]")
            break
        
        else:
            console.print("[red]Invalid choice, try again.[/]")